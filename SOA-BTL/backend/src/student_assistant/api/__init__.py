"""Đăng ký các Blueprint REST API của AI Student Assistant."""

from flask import Flask

from ..modules.auth.api import bp as auth_bp
from ..modules.chat.api import bp as chat_bp
from ..modules.comments.api import bp as comments_bp
from ..modules.documents.api import bp as documents_bp
from ..modules.grade_planning.api import bp as grade_planning_bp
from ..modules.quiz_review.api import bp as quiz_reviews_bp
from ..modules.recommendations.api import bp as recommendations_bp


def register_blueprints(app: Flask) -> None:
    """Gắn các nhóm API vào ứng dụng; các Blueprint chưa có route nghiệp vụ."""
    blueprints = (
        (auth_bp, "/api/v1/auth"),
        (chat_bp, "/api/v1/chat"),
        (documents_bp, "/api/v1/documents"),
        (quiz_reviews_bp, "/api/v1/quiz-reviews"),
        (grade_planning_bp, "/api/v1/grade-planning"),
        (comments_bp, "/api/v1/comments"),
        (recommendations_bp, "/api/v1/recommendations"),
    )
    for blueprint, prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=prefix)
