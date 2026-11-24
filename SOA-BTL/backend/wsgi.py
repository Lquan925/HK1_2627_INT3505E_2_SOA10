"""WSGI entry point; run from backend after installing the package."""

from student_assistant import create_app

app = create_app()
