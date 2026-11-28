"""Create and configure independent Flask application instances."""

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from .api import register_blueprints
from .api.docs import register_api_docs
from .config import get_config
from .extensions import db, migrate


def create_app(config: dict | None = None) -> Flask:
    """Initialize the scaffold; business endpoints will be added later."""
    load_dotenv(Path.cwd() / ".env")

    app = Flask(__name__)
    app.config.from_mapping(get_config())
    if config is not None:
        app.config.update(config)

    db.init_app(app)

    # Register all ERD tables before Alembic or the CLI accesses metadata.
    from .modules.auth import models as auth_models  # noqa: F401
    from .modules.chat import models as chat_models  # noqa: F401
    from .modules.documents import models as document_models  # noqa: F401
    from .modules.grade_planning import models as grade_models  # noqa: F401
    from .modules.quiz_review import models as quiz_models  # noqa: F401
    from .modules.recommendations import models as recommendation_models  # noqa: F401

    migrate.init_app(app, db, directory="migrations")
    register_blueprints(app)
    register_api_docs(app)
    from .seed import register_seed_commands

    register_seed_commands(app)
    return app
