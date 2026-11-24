"""Read backend settings from the environment at app creation time."""

import os

from sqlalchemy.engine import URL


def get_database_url() -> str | URL:
    """Ưu tiên URL có sẵn; ghép thông tin Docker mà không lỗi ký tự mật khẩu."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    if os.getenv("DB_HOST"):
        return URL.create(
            "postgresql+psycopg",
            username=os.getenv("DB_USER", "ai_student_assistant"),
            password=os.getenv("DB_PASSWORD"),
            host=os.environ["DB_HOST"],
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "ai_student_assistant"),
        )
    return "postgresql+psycopg://localhost/ai_student_assistant"


def get_config() -> dict:
    """Keep provider secrets on the backend and out of source control."""
    return {
        "SECRET_KEY": os.getenv("SECRET_KEY") or None,
        "SQLALCHEMY_DATABASE_URI": get_database_url(),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "OPENAPI_SPEC_DIR": os.getenv("OPENAPI_SPEC_DIR") or None,
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", ""),
        "LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
        "LLM_MODEL": os.getenv("LLM_MODEL", ""),
        "EMBEDDING_PROVIDER": os.getenv("EMBEDDING_PROVIDER", ""),
        "EMBEDDING_API_KEY": os.getenv("EMBEDDING_API_KEY", ""),
        "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", ""),
        "AI_REQUEST_TIMEOUT_SECONDS": int(
            os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "30")
        ),
        "AI_MAX_RETRIES": int(os.getenv("AI_MAX_RETRIES", "2")),
    }
