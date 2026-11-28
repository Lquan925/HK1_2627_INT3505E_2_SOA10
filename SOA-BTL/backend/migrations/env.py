"""Connect Alembic to the active Flask app and SQLAlchemy metadata."""

from alembic import context
from flask import current_app

migration_extension = current_app.extensions["migrate"]
database = migration_extension.db
migration_options = dict(migration_extension.configure_args)
migration_options.setdefault(
    "include_object",
    lambda obj, name, kind, reflected, compare_to:
        not (kind == "table" and name == "alembic_version"),
)

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
            # Keep revision tracking in the active schema, including isolated
            # test schemas when public already has its own alembic_version.
            version_table_schema=connection.dialect.default_schema_name,
            **migration_options,
        )
        with context.begin_transaction():
            context.run_migrations()
