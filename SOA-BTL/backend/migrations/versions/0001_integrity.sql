-- Frozen integrity rules for revision 0001_initial. Runtime consent, expiry,
-- source permission and filtering remain responsibilities of application services.

CREATE FUNCTION prevent_erd_identity_change() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE field_name text;
BEGIN
    FOREACH field_name IN ARRAY TG_ARGV LOOP
        IF to_jsonb(OLD)->field_name IS DISTINCT FROM to_jsonb(NEW)->field_name THEN
            RAISE EXCEPTION 'Identity field %.% cannot be changed', TG_TABLE_NAME, field_name
                USING ERRCODE = '23514';
        END IF;
    END LOOP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER immutable_document_scope BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION prevent_erd_identity_change('id', 'client_session_id', 'course_id', 'external_doc_id');
CREATE TRIGGER immutable_chat_scope BEFORE UPDATE ON chat_sessions
FOR EACH ROW EXECUTE FUNCTION prevent_erd_identity_change('id', 'client_session_id', 'course_id', 'mode');
CREATE TRIGGER immutable_message_scope BEFORE UPDATE ON chat_messages
FOR EACH ROW EXECUTE FUNCTION prevent_erd_identity_change('id', 'chat_session_id', 'role', 'message_type');
CREATE TRIGGER immutable_chunk_source BEFORE UPDATE ON document_chunks
FOR EACH ROW EXECUTE FUNCTION prevent_erd_identity_change('id', 'document_id', 'index_generation', 'chunk_index', 'content', 'source_revision', 'embedding_model', 'embedding');
CREATE TRIGGER immutable_topic_scope BEFORE UPDATE ON knowledge_topics
FOR EACH ROW EXECUTE FUNCTION prevent_erd_identity_change('id', 'client_session_id', 'course_id');
CREATE TRIGGER immutable_review_scope BEFORE UPDATE ON quiz_reviews
FOR EACH ROW EXECUTE FUNCTION prevent_erd_identity_change('id', 'client_session_id', 'course_id', 'data_source', 'used_data_categories');
CREATE TRIGGER immutable_analysis_scope BEFORE UPDATE ON learning_analyses
FOR EACH ROW EXECUTE FUNCTION prevent_erd_identity_change('id', 'client_session_id', 'course_id');
CREATE TRIGGER immutable_grade_scope BEFORE UPDATE ON grade_goals
FOR EACH ROW EXECUTE FUNCTION prevent_erd_identity_change('id', 'client_session_id', 'course_id', 'scope_type', 'quiz_group_id', 'data_source', 'max_scale', 'grading_rule');
CREATE TRIGGER immutable_message_document_scope BEFORE UPDATE ON message_documents
FOR EACH ROW EXECUTE FUNCTION prevent_erd_identity_change('message_id', 'document_id');

CREATE FUNCTION validate_consent_courses() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE consent_uuid uuid; consent_scope text; course_count bigint;
BEGIN
    -- Check both sides of a moved course row. Deferred checks allow inserting a
    -- SELECTED_COURSES consent and its course rows in the same transaction.
    FOR consent_uuid IN
        SELECT DISTINCT value::uuid FROM unnest(ARRAY[
            CASE WHEN TG_OP <> 'INSERT' THEN
                CASE WHEN TG_TABLE_NAME = 'data_consents' THEN to_jsonb(OLD)->>'id'
                     ELSE to_jsonb(OLD)->>'consent_id' END END,
            CASE WHEN TG_OP <> 'DELETE' THEN
                CASE WHEN TG_TABLE_NAME = 'data_consents' THEN to_jsonb(NEW)->>'id'
                     ELSE to_jsonb(NEW)->>'consent_id' END END
        ]) AS ids(value) WHERE value IS NOT NULL
    LOOP
        SELECT scope_type INTO consent_scope FROM data_consents WHERE id = consent_uuid FOR UPDATE;
        IF NOT FOUND THEN CONTINUE; END IF;
        SELECT count(*) INTO course_count FROM consent_courses WHERE consent_id = consent_uuid;
        IF (consent_scope = 'SELECTED_COURSES' AND course_count = 0) OR
           (consent_scope = 'ALL_AUTHORIZED_COURSES' AND course_count <> 0) THEN
            RAISE EXCEPTION 'Consent course rows do not match scope %', consent_scope
                USING ERRCODE = '23514';
        END IF;
    END LOOP;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER consent_scope_courses AFTER INSERT OR UPDATE ON data_consents
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_consent_courses();
CREATE CONSTRAINT TRIGGER consent_course_membership AFTER INSERT OR UPDATE OR DELETE ON consent_courses
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_consent_courses();

CREATE FUNCTION validate_message_document_scope() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE valid_link boolean;
BEGIN
    IF TG_OP = 'DELETE' THEN
        -- Deleting the whole message is fine; deleting one of the documents
        -- while keeping a citation to it would lose the full source scope.
        IF EXISTS (SELECT 1 FROM chat_messages WHERE id = OLD.message_id) AND EXISTS (
            SELECT 1 FROM chat_citations c JOIN document_chunks k ON k.id = c.chunk_id
            WHERE c.message_id = OLD.message_id AND k.document_id = OLD.document_id
        ) THEN
            RAISE EXCEPTION 'Remove dependent citations before removing a source document'
                USING ERRCODE = '23514';
        END IF;
        RETURN OLD;
    END IF;
    SELECT s.client_session_id = d.client_session_id
       AND s.mode <> 'GENERAL'
       AND (s.mode = 'MULTI_COURSE_SUMMARY' OR s.course_id = d.course_id)
       AND ((m.message_type = 'CHAT' AND NEW.used_purpose = 'KNOWLEDGE_QA') OR
            (m.message_type = 'SUMMARY' AND NEW.used_purpose = 'DOCUMENT_SUMMARY'))
    INTO valid_link
    FROM chat_messages m JOIN chat_sessions s ON s.id = m.chat_session_id
    CROSS JOIN documents d
    WHERE m.id = NEW.message_id AND d.id = NEW.document_id;
    IF valid_link IS NOT TRUE THEN
        RAISE EXCEPTION 'Message document must match its owner, course and purpose'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER message_document_scope BEFORE INSERT OR UPDATE OR DELETE ON message_documents
FOR EACH ROW EXECUTE FUNCTION validate_message_document_scope();

CREATE FUNCTION validate_citation_scope() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE valid_link boolean;
BEGIN
    SELECT s.client_session_id = d.client_session_id AND m.role = 'ASSISTANT'
       AND s.mode <> 'GENERAL'
       AND (s.mode = 'MULTI_COURSE_SUMMARY' OR s.course_id = d.course_id)
       AND EXISTS (SELECT 1 FROM message_documents md
                   WHERE md.message_id = m.id AND md.document_id = d.id)
    INTO valid_link
    FROM chat_messages m JOIN chat_sessions s ON s.id = m.chat_session_id
    CROSS JOIN document_chunks k JOIN documents d ON d.id = k.document_id
    WHERE m.id = NEW.message_id AND k.id = NEW.chunk_id;
    IF valid_link IS NOT TRUE THEN
        RAISE EXCEPTION 'Citation must be an assistant source in the same owner/course scope'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER citation_scope BEFORE INSERT OR UPDATE ON chat_citations
FOR EACH ROW EXECUTE FUNCTION validate_citation_scope();

CREATE FUNCTION validate_quiz_topic_scope() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.topic_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM quiz_reviews r JOIN knowledge_topics t
          ON t.client_session_id = r.client_session_id AND t.course_id = r.course_id
        WHERE r.id = NEW.review_id AND t.id = NEW.topic_id
    ) THEN
        RAISE EXCEPTION 'Quiz topic must belong to the review owner and course'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER quiz_topic_scope BEFORE INSERT OR UPDATE ON quiz_review_items
FOR EACH ROW EXECUTE FUNCTION validate_quiz_topic_scope();

CREATE FUNCTION validate_analysis_document_scope() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM learning_analyses a JOIN documents d
          ON d.client_session_id = a.client_session_id AND d.course_id = a.course_id
        WHERE a.id = NEW.analysis_id AND d.id = NEW.document_id
    ) THEN
        RAISE EXCEPTION 'Analysis document must match its owner and course'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER analysis_document_scope BEFORE INSERT OR UPDATE ON analysis_documents
FOR EACH ROW EXECUTE FUNCTION validate_analysis_document_scope();

CREATE FUNCTION validate_recommendation_scope() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM learning_analyses a JOIN knowledge_topics t
          ON t.client_session_id = a.client_session_id AND t.course_id = a.course_id
        WHERE a.id = NEW.analysis_id AND t.id = NEW.topic_id
    ) OR (NEW.related_document_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM learning_analyses a JOIN documents d
          ON d.client_session_id = a.client_session_id AND d.course_id = a.course_id
        WHERE a.id = NEW.analysis_id AND d.id = NEW.related_document_id
    )) THEN
        RAISE EXCEPTION 'Recommendation references must match its owner and course'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER recommendation_scope BEFORE INSERT OR UPDATE ON learning_recommendations
FOR EACH ROW EXECUTE FUNCTION validate_recommendation_scope();

CREATE FUNCTION validate_document_generation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE doc_uuid uuid; generation uuid; current_status text;
BEGIN
    FOR doc_uuid IN
        SELECT DISTINCT value::uuid FROM unnest(ARRAY[
            CASE WHEN TG_OP <> 'INSERT' THEN
                CASE WHEN TG_TABLE_NAME = 'documents' THEN to_jsonb(OLD)->>'id'
                     ELSE to_jsonb(OLD)->>'document_id' END END,
            CASE WHEN TG_OP <> 'DELETE' THEN
                CASE WHEN TG_TABLE_NAME = 'documents' THEN to_jsonb(NEW)->>'id'
                     ELSE to_jsonb(NEW)->>'document_id' END END
        ]) AS ids(value) WHERE value IS NOT NULL
    LOOP
        SELECT active_index_generation, index_status INTO generation, current_status
        FROM documents WHERE id = doc_uuid FOR UPDATE;
        IF NOT FOUND THEN CONTINUE; END IF;
        IF current_status = 'INDEXED' AND NOT EXISTS (
            SELECT 1 FROM document_chunks WHERE document_id = doc_uuid AND index_generation = generation
        ) THEN
            RAISE EXCEPTION 'Indexed documents need chunks in the active generation'
                USING ERRCODE = '23514';
        END IF;
        IF EXISTS (
            SELECT 1 FROM document_chunks WHERE document_id = doc_uuid
            GROUP BY index_generation
            HAVING count(DISTINCT embedding_model) > 1 OR count(DISTINCT vector_dims(embedding)) > 1
        ) THEN
            RAISE EXCEPTION 'Each document generation must use one embedding model and dimension'
                USING ERRCODE = '23514';
        END IF;
    END LOOP;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER document_active_generation AFTER INSERT OR UPDATE ON documents
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_document_generation();
CREATE CONSTRAINT TRIGGER document_chunk_generation AFTER INSERT OR UPDATE OR DELETE ON document_chunks
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_document_generation();
