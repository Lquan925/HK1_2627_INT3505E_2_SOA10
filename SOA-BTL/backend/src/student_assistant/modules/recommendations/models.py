"""Learning analysis, observed evidence and recommendations from the ERD."""

from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from ...extensions import db


class KnowledgeTopic(db.Model):
    __tablename__ = "knowledge_topics"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    client_session_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("client_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.Index("ix_knowledge_topics_owner_course", "client_session_id", "course_id"),
        db.CheckConstraint(
            "btrim(course_id) <> '' AND btrim(name) <> ''",
            name="ck_knowledge_topics_identity",
        ),
    )


class LearningAnalysis(db.Model):
    __tablename__ = "learning_analyses"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    client_session_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("client_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id = db.Column(db.Text, nullable=False)
    focus_topic = db.Column(db.Text, nullable=True)
    has_sufficient_data = db.Column(db.Boolean, nullable=False)
    data_limitations = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    __table_args__ = (
        db.Index("ix_learning_analyses_owner_course", "client_session_id", "course_id"),
        db.CheckConstraint("btrim(course_id) <> ''", name="ck_learning_analyses_course"),
    )


class LearningEvidence(db.Model):
    __tablename__ = "learning_evidence"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("learning_analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_quiz_id = db.Column(db.Text, nullable=False)
    portal_attempt_id = db.Column(db.Text, nullable=True)
    question_number = db.Column(db.Integer, nullable=False)
    topic_name = db.Column(db.Text, nullable=True)
    question_text = db.Column(db.Text, nullable=False)
    student_answer = db.Column(db.Text, nullable=False)
    official_points = db.Column(db.Numeric, nullable=False)
    max_points = db.Column(db.Numeric, nullable=False)
    data_source = db.Column(db.Text, nullable=False)
    used_data_categories = db.Column(ARRAY(db.Text), nullable=False)

    __table_args__ = (
        db.Index("ix_learning_evidence_analysis", "analysis_id"),
        db.CheckConstraint(
            "question_number >= 1", name="ck_learning_evidence_question_number"
        ),
        db.CheckConstraint(
            "btrim(external_quiz_id) <> '' AND btrim(question_text) <> ''",
            name="ck_learning_evidence_identity",
        ),
        db.CheckConstraint(
            "max_points > 0 AND max_points < 'Infinity'::numeric "
            "AND official_points >= 0 AND official_points <= max_points",
            name="ck_learning_evidence_points",
        ),
        db.CheckConstraint(
            "data_source IN ('PORTAL', 'MANUAL')",
            name="ck_learning_evidence_data_source",
        ),
        db.CheckConstraint(
            "used_data_categories <@ ARRAY['QUIZ_SUBMISSIONS', 'GRADE_BOOK']::text[] "
            "AND array_position(used_data_categories, NULL) IS NULL",
            name="ck_learning_evidence_categories",
        ),
        db.CheckConstraint(
            "(data_source = 'MANUAL' AND cardinality(used_data_categories) = 0) OR "
            "(data_source = 'PORTAL' AND cardinality(used_data_categories) > 0)",
            name="ck_learning_evidence_source_categories",
        ),
    )


class LearningRecommendation(db.Model):
    __tablename__ = "learning_recommendations"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("learning_analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("knowledge_topics.id", ondelete="RESTRICT"),
        nullable=False,
    )
    priority_rank = db.Column(db.Integer, nullable=False)
    weakness_reason = db.Column(db.Text, nullable=False)
    study_advice = db.Column(db.Text, nullable=False)
    observed_evidence = db.Column(JSONB, nullable=False)
    ai_inference = db.Column(db.Text, nullable=False)
    related_document_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=True,
    )
    related_document_title = db.Column(db.Text, nullable=True)
    related_document_note = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint(
            "analysis_id", "priority_rank", name="uq_learning_recommendations_priority"
        ),
        db.Index("ix_learning_recommendations_topic", "topic_id"),
        db.Index("ix_learning_recommendations_document", "related_document_id"),
        db.CheckConstraint(
            "priority_rank >= 1", name="ck_learning_recommendations_priority"
        ),
        db.CheckConstraint(
            "CASE WHEN jsonb_typeof(observed_evidence) = 'array' "
            "THEN jsonb_array_length(observed_evidence) > 0 "
            "AND NOT jsonb_path_exists(observed_evidence, '$[*] ? (@.type() != \"string\")') "
            "ELSE false END",
            name="ck_learning_recommendations_evidence",
        ),
    )


class AnalysisDocument(db.Model):
    __tablename__ = "analysis_documents"

    analysis_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("learning_analyses.id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("documents.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    source_revision_snapshot = db.Column(db.Text, nullable=True)

    __table_args__ = (db.Index("ix_analysis_documents_document", "document_id"),)
