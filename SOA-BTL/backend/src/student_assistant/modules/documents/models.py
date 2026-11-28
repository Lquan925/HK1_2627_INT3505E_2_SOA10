"""Document sources and versioned chunks used by RAG.

Vector() preserves the ERD's unspecified D. Query services must select the same
embedding_model and dimension as the query. Add a dimensioned column/ANN index
in a later migration once the embedding provider has been agreed.
"""

from uuid import uuid4

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from ...extensions import db


class Document(db.Model):
    __tablename__ = "documents"
    __table_args__ = (
        sa.UniqueConstraint("client_session_id", "course_id", "external_doc_id", name="uq_documents_owner_course_external"),
        sa.CheckConstraint("length(btrim(course_id)) > 0 AND length(btrim(external_doc_id)) > 0 AND length(btrim(title)) > 0", name="ck_documents_required_text"),
        sa.CheckConstraint("index_status IN ('PENDING', 'INDEXED', 'FAILED')", name="ck_documents_index_status"),
        sa.CheckConstraint("index_status <> 'INDEXED' OR active_index_generation IS NOT NULL", name="ck_documents_active_index"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    client_session_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("client_sessions.id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Text, nullable=False)
    external_doc_id = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.Text, nullable=True)
    source_revision = db.Column(db.Text, nullable=True)
    active_index_generation = db.Column(db.Uuid(as_uuid=True), nullable=True)
    index_status = db.Column(db.Text, nullable=False, server_default="PENDING")
    is_partial_content = db.Column(db.Boolean, nullable=False, server_default=sa.false())
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())


class DocumentAccess(db.Model):
    __tablename__ = "document_access"
    __table_args__ = (
        sa.CheckConstraint("length(btrim(access_status)) > 0 AND length(btrim(permission_source)) > 0", name="ck_document_access_required_text"),
    )

    document_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    access_status = db.Column(db.Text, nullable=False)
    last_checked_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    permission_source = db.Column(db.Text, nullable=False)


class DocumentChunk(db.Model):
    __tablename__ = "document_chunks"
    __table_args__ = (
        sa.UniqueConstraint("document_id", "index_generation", "chunk_index", name="uq_document_chunks_generation_position"),
        sa.CheckConstraint("chunk_index >= 0", name="ck_document_chunks_position"),
        sa.CheckConstraint("length(btrim(content)) > 0 AND length(btrim(embedding_model)) > 0", name="ck_document_chunks_required_text"),
        sa.Index("ix_document_chunks_embedding_model", "embedding_model"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    document_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    index_generation = db.Column(db.Uuid(as_uuid=True), nullable=False)
    source_revision = db.Column(db.Text, nullable=True)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    location_label = db.Column(db.Text, nullable=True)
    embedding = db.Column(Vector(), nullable=False)
    embedding_model = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
