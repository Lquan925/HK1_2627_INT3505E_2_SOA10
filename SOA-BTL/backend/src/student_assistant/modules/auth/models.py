"""Anonymous application sessions and purpose-specific data consent.

Only application-token hashes are persisted, never Portal credentials. The
migration checks consent/course cardinality with deferred constraints; services
must still check expiry and current consent before accessing data.
"""

from uuid import uuid4

import sqlalchemy as sa

from ...extensions import db


class ClientSession(db.Model):
    __tablename__ = "client_sessions"
    __table_args__ = (
        sa.UniqueConstraint("token_hash", name="uq_client_sessions_token_hash"),
        sa.CheckConstraint("length(btrim(token_hash)) > 0", name="ck_client_sessions_token_hash"),
        sa.CheckConstraint("expires_at > created_at", name="ck_client_sessions_expiry"),
        sa.CheckConstraint("revoked_at IS NULL OR revoked_at >= created_at", name="ck_client_sessions_revocation"),
        sa.Index("ix_client_sessions_expires_at", "expires_at"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    token_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)


class DataConsent(db.Model):
    __tablename__ = "data_consents"
    __table_args__ = (
        sa.UniqueConstraint("client_session_id", "data_category", "purpose", name="uq_data_consents_owner_category_purpose"),
        sa.CheckConstraint(
            "(data_category = 'COURSE_DOCUMENTS' AND purpose IN "
            "('KNOWLEDGE_QA', 'KNOWLEDGE_SEARCH', 'DOCUMENT_SUMMARY', 'LEARNING_ANALYSIS')) OR "
            "(data_category = 'QUIZ_SUBMISSIONS' AND purpose IN "
            "('QUIZ_REVIEW', 'COMMENT_SUGGESTION', 'LEARNING_ANALYSIS')) OR "
            "(data_category = 'GRADE_BOOK' AND purpose IN "
            "('GRADE_PLANNING', 'LEARNING_ANALYSIS', 'QUIZ_REVIEW', 'COMMENT_SUGGESTION'))",
            name="ck_data_consents_category_purpose",
        ),
        sa.CheckConstraint("scope_type IN ('SELECTED_COURSES', 'ALL_AUTHORIZED_COURSES')", name="ck_data_consents_scope_type"),
        sa.CheckConstraint("NOT is_granted OR (granted_at IS NOT NULL AND revoked_at IS NULL)", name="ck_data_consents_grant_state"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    client_session_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("client_sessions.id", ondelete="CASCADE"), nullable=False)
    data_category = db.Column(db.Text, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    is_granted = db.Column(db.Boolean, nullable=False, server_default=sa.false())
    scope_type = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    granted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)


class ConsentCourse(db.Model):
    __tablename__ = "consent_courses"
    __table_args__ = (
        sa.CheckConstraint("length(btrim(course_id)) > 0", name="ck_consent_courses_course_id"),
    )

    consent_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("data_consents.id", ondelete="CASCADE"), primary_key=True)
    course_id = db.Column(db.Text, primary_key=True)
