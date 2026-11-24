"""Connect Alembic to the active Flask app and SQLAlchemy metadata."""

from alembic import context
from flask import current_app

migration_extension = current_app.extensions["migrate"]
database = migration_extension.db
migration_options = dict(migration_extension.configure_args)

if context.is_offline_mode():
    context.configure(
        url=database.engine.url.render_as_string(hide_password=False),
        target_metadata=database.metadata,
        literal_binds=True,
        **migration_options,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    with database.engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=database.metadata,
            **migration_options,
        )
        with context.begin_transaction():
            context.run_migrations()
