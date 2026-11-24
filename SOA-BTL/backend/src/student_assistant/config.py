"""Read backend settings from the environment at app creation time."""

import os


def get_config() -> dict:
    """Keep provider secrets on the backend and out of source control."""
    return {
        "SECRET_KEY": os.getenv("SECRET_KEY") or None,
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://localhost/ai_student_assistant",
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
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
