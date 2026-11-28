"""Conversation history, citations and the complete source-document scope."""

from uuid import uuid4

import sqlalchemy as sa

from ...extensions import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        sa.CheckConstraint("mode IN ('GENERAL', 'COURSE_CONTEXT', 'MULTI_COURSE_SUMMARY')", name="ck_chat_sessions_mode"),
        sa.CheckConstraint(
            "(mode = 'COURSE_CONTEXT' AND course_id IS NOT NULL AND length(btrim(course_id)) > 0) OR "
            "(mode IN ('GENERAL', 'MULTI_COURSE_SUMMARY') AND course_id IS NULL AND course_name IS NULL)",
            name="ck_chat_sessions_course_scope",
        ),
        sa.Index("ix_chat_sessions_owner_course_created", "client_session_id", "course_id", "created_at"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    client_session_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("client_sessions.id", ondelete="CASCADE"), nullable=False)
    mode = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Text, nullable=True)
    course_name = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    __table_args__ = (
        sa.CheckConstraint("role IN ('USER', 'ASSISTANT')", name="ck_chat_messages_role"),
        sa.CheckConstraint("message_type IN ('CHAT', 'SUMMARY')", name="ck_chat_messages_type"),
        sa.CheckConstraint("length(btrim(content)) > 0", name="ck_chat_messages_content"),
        sa.CheckConstraint(
            "(role = 'USER' AND answer_status IS NULL AND NOT has_external_knowledge AND external_knowledge_note IS NULL) OR "
            "(role = 'ASSISTANT' AND answer_status IS NOT NULL AND answer_status IN ('ANSWERED', 'INSUFFICIENT_CONTEXT'))",
            name="ck_chat_messages_answer_state",
        ),
        sa.CheckConstraint(
            "(message_type = 'CHAT' AND NOT is_partial_content AND coverage_note IS NULL) OR "
            "(message_type = 'SUMMARY' AND role = 'ASSISTANT' AND coverage_note IS NOT NULL AND length(btrim(coverage_note)) > 0)",
            name="ck_chat_messages_summary_state",
        ),
        sa.CheckConstraint(
            "(NOT has_external_knowledge AND external_knowledge_note IS NULL) OR "
            "(has_external_knowledge AND external_knowledge_note IS NOT NULL AND length(btrim(external_knowledge_note)) > 0)",
            name="ck_chat_messages_external_knowledge",
        ),
        sa.Index("ix_chat_messages_session_created", "chat_session_id", "created_at"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    chat_session_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.Text, nullable=False, server_default="CHAT")
    content = db.Column(db.Text, nullable=False)
    answer_status = db.Column(db.Text, nullable=True)
    has_external_knowledge = db.Column(db.Boolean, nullable=False, server_default=sa.false())
    external_knowledge_note = db.Column(db.Text, nullable=True)
    is_partial_content = db.Column(db.Boolean, nullable=False, server_default=sa.false())
    coverage_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


class ChatCitation(db.Model):
    __tablename__ = "chat_citations"
    __table_args__ = (
        sa.CheckConstraint("length(btrim(quoted_snippet)) > 0 AND length(btrim(document_title_snapshot)) > 0", name="ck_chat_citations_required_text"),
        sa.Index("ix_chat_citations_message", "message_id"),
        sa.Index("ix_chat_citations_chunk", "chunk_id"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    message_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    chunk_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("document_chunks.id", ondelete="RESTRICT"), nullable=False)
    quoted_snippet = db.Column(db.Text, nullable=False)
    document_title_snapshot = db.Column(db.Text, nullable=False)
    location_label = db.Column(db.Text, nullable=True)


class MessageDocument(db.Model):
    __tablename__ = "message_documents"
    __table_args__ = (
        sa.CheckConstraint("used_purpose IN ('KNOWLEDGE_QA', 'DOCUMENT_SUMMARY')", name="ck_message_documents_used_purpose"),
        sa.Index("ix_message_documents_document", "document_id"),
    )

    message_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("chat_messages.id", ondelete="CASCADE"), primary_key=True)
    document_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("documents.id", ondelete="RESTRICT"), primary_key=True)
    source_revision_snapshot = db.Column(db.Text, nullable=True)
    used_purpose = db.Column(db.Text, nullable=False)
