"""Kiểm tra cấu hình kết nối khi chạy cục bộ và trong Docker."""

import pytest
from sqlalchemy.engine import make_url

from student_assistant.config import get_config


@pytest.fixture(autouse=True)
def clear_database_environment(monkeypatch):
    for name in ["DATABASE_URL", "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]:
        monkeypatch.delenv(name, raising=False)


def test_explicit_database_url_takes_precedence(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("DB_HOST", "db")
    assert get_config()["SQLALCHEMY_DATABASE_URI"] == "sqlite://"


def test_docker_database_credentials_preserve_special_characters(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "student_assistant")
    monkeypatch.setenv("DB_USER", "student")
    monkeypatch.setenv("DB_PASSWORD", "test:p@ss/word?#%")
    url = make_url(get_config()["SQLALCHEMY_DATABASE_URI"])
    assert url.host == "db"
    assert url.port == 5432
    assert url.database == "student_assistant"
    assert url.username == "student"
    assert url.password == "test:p@ss/word?#%"


def test_default_database_remains_local():
    url = make_url(get_config()["SQLALCHEMY_DATABASE_URI"])
    assert url.drivername == "postgresql+psycopg"
    assert url.host == "localhost"
    assert url.database == "ai_student_assistant"
