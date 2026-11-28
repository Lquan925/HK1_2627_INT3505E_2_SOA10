"""Stored quiz evidence and advisory assessments; never official grade changes."""

from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from ...extensions import db


class QuizReview(db.Model):
    __tablename__ = "quiz_reviews"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    client_session_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("client_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id = db.Column(db.Text, nullable=False)
    external_quiz_id = db.Column(db.Text, nullable=False)
    quiz_title = db.Column(db.Text, nullable=False)
    portal_attempt_id = db.Column(db.Text, nullable=True)
    quiz_status = db.Column(db.Text, nullable=False)
    data_source = db.Column(db.Text, nullable=False)
    used_data_categories = db.Column(ARRAY(db.Text), nullable=False)
    is_complete_attempt = db.Column(db.Boolean, nullable=False)
    official_total_score = db.Column(db.Numeric, nullable=True)
    ai_estimated_total_score = db.Column(db.Numeric, nullable=True)
    portal_official_score = db.Column(db.Numeric, nullable=True)
    portal_max_score = db.Column(db.Numeric, nullable=True)
    has_complete_rubric = db.Column(db.Boolean, nullable=False)
    assessment_status = db.Column(db.Text, nullable=False)
    assessment_limitations = db.Column(db.Text, nullable=True)
    disclaimer = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    __table_args__ = (
        db.Index("ix_quiz_reviews_owner_course", "client_session_id", "course_id"),
        db.CheckConstraint("btrim(course_id) <> ''", name="ck_quiz_reviews_course"),
        db.CheckConstraint(
            "btrim(external_quiz_id) <> '' AND btrim(quiz_title) <> ''",
            name="ck_quiz_reviews_source_identity",
        ),
        db.CheckConstraint("quiz_status = 'GRADED'", name="ck_quiz_reviews_status"),
        db.CheckConstraint(
            "data_source IN ('PORTAL', 'MANUAL')", name="ck_quiz_reviews_data_source"
        ),
        db.CheckConstraint(
            "used_data_categories <@ ARRAY['QUIZ_SUBMISSIONS', 'GRADE_BOOK']::text[] "
            "AND array_position(used_data_categories, NULL) IS NULL",
            name="ck_quiz_reviews_categories",
        ),
        db.CheckConstraint(
            "(data_source = 'MANUAL' AND cardinality(used_data_categories) = 0) OR "
            "(data_source = 'PORTAL' AND cardinality(used_data_categories) > 0)",
            name="ck_quiz_reviews_source_categories",
        ),
        db.CheckConstraint(
            "assessment_status IN ('COMPLETE', 'PARTIAL', 'QUALITATIVE_ONLY')",
            name="ck_quiz_reviews_assessment_status",
        ),
        db.CheckConstraint(
            "official_total_score IS NULL OR "
            "(is_complete_attempt AND official_total_score >= 0 "
            "AND official_total_score < 'Infinity'::numeric)",
            name="ck_quiz_reviews_official_total",
        ),
        db.CheckConstraint(
            "ai_estimated_total_score IS NULL OR "
            "(is_complete_attempt AND has_complete_rubric "
            "AND ai_estimated_total_score >= 0 "
            "AND ai_estimated_total_score < 'Infinity'::numeric)",
            name="ck_quiz_reviews_ai_total",
        ),
        db.CheckConstraint(
            "portal_max_score IS NULL OR "
            "(portal_max_score > 0 AND portal_max_score < 'Infinity'::numeric)",
            name="ck_quiz_reviews_portal_max",
        ),
        db.CheckConstraint(
            "portal_official_score IS NULL OR (portal_official_score >= 0 "
            "AND portal_official_score < 'Infinity'::numeric "
            "AND (portal_max_score IS NULL OR portal_official_score <= portal_max_score))",
            name="ck_quiz_reviews_portal_score",
        ),
        db.CheckConstraint(
            "assessment_status <> 'COMPLETE' OR "
            "(is_complete_attempt AND has_complete_rubric)",
            name="ck_quiz_reviews_complete_assessment",
        ),
        db.CheckConstraint("btrim(disclaimer) <> ''", name="ck_quiz_reviews_disclaimer"),
    )


class QuizReviewItem(db.Model):
    __tablename__ = "quiz_review_items"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    review_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("quiz_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("knowledge_topics.id", ondelete="RESTRICT"),
        nullable=True,
    )
    question_number = db.Column(db.Integer, nullable=False)
    question_type = db.Column(db.Text, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    student_answer = db.Column(db.Text, nullable=False)
    correct_answer_or_rubric = db.Column(db.Text, nullable=True)
    official_points = db.Column(db.Numeric, nullable=False)
    max_points = db.Column(db.Numeric, nullable=False)
    ai_estimated_points = db.Column(db.Numeric, nullable=True)
    is_discrepant = db.Column(db.Boolean, nullable=True)
    explanation = db.Column(db.Text, nullable=False)
    assessment_limitations = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("review_id", "question_number", name="uq_quiz_item_question"),
        db.Index("ix_quiz_review_items_topic", "topic_id"),
        db.CheckConstraint("question_number >= 1", name="ck_quiz_items_number"),
        db.CheckConstraint(
            "question_type IN ('MULTIPLE_CHOICE', 'ESSAY')", name="ck_quiz_items_type"
        ),
        db.CheckConstraint("btrim(question_text) <> ''", name="ck_quiz_items_question"),
        db.CheckConstraint(
            "max_points > 0 AND max_points < 'Infinity'::numeric "
            "AND official_points >= 0 AND official_points <= max_points",
            name="ck_quiz_items_official_points",
        ),
        db.CheckConstraint(
            "ai_estimated_points IS NULL OR "
            "(correct_answer_or_rubric IS NOT NULL "
            "AND btrim(correct_answer_or_rubric) <> '' "
            "AND ai_estimated_points >= 0 AND ai_estimated_points <= max_points)",
            name="ck_quiz_items_ai_points",
        ),
        db.CheckConstraint(
            "ai_estimated_points IS NOT NULL OR is_discrepant IS NULL",
            name="ck_quiz_items_discrepancy_basis",
        ),
    )
