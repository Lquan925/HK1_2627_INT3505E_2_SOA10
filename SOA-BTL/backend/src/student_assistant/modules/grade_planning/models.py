"""Persisted grade goals; calculation inputs and outputs remain stateless."""

from uuid import uuid4

import sqlalchemy as sa

from ...extensions import db


class GradeGoal(db.Model):
    __tablename__ = "grade_goals"
    __table_args__ = (
        sa.CheckConstraint("length(btrim(course_id)) > 0", name="ck_grade_goals_course_id"),
        sa.CheckConstraint("scope_type IN ('QUIZ_AVERAGE', 'COURSE_FINAL')", name="ck_grade_goals_scope_type"),
        sa.CheckConstraint(
            "(scope_type = 'QUIZ_AVERAGE' AND quiz_group_id IS NOT NULL AND length(btrim(quiz_group_id)) > 0) OR "
            "(scope_type = 'COURSE_FINAL' AND quiz_group_id IS NULL)",
            name="ck_grade_goals_quiz_group",
        ),
        sa.CheckConstraint("max_scale >= 1 AND target_score >= 0 AND target_score <= max_scale", name="ck_grade_goals_score_range"),
        sa.CheckConstraint("grading_rule = 'WEIGHTED_AVERAGE'", name="ck_grade_goals_grading_rule"),
        sa.CheckConstraint("data_source IN ('PORTAL', 'MANUAL')", name="ck_grade_goals_data_source"),
        sa.Index("uq_grade_goals_course_final", "client_session_id", "course_id", "scope_type", unique=True, postgresql_where=sa.text("quiz_group_id IS NULL")),
        sa.Index("uq_grade_goals_quiz_group", "client_session_id", "course_id", "scope_type", "quiz_group_id", unique=True, postgresql_where=sa.text("quiz_group_id IS NOT NULL")),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    client_session_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("client_sessions.id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Text, nullable=False)
    scope_type = db.Column(db.Text, nullable=False)
    quiz_group_id = db.Column(db.Text, nullable=True)
    target_score = db.Column(db.Numeric, nullable=False)
    max_scale = db.Column(db.Numeric, nullable=False)
    grading_rule = db.Column(db.Text, nullable=False)
    data_source = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
