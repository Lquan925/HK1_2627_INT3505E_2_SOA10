"""Small, idempotent development fixtures; no fabricated AI or vector results."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import NAMESPACE_URL, uuid5

import click
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db


def demo_id(name):
    """Keep fixture identifiers stable across machines and repeated runs."""
    return uuid5(NAMESPACE_URL, "https://student-assistant.example/demo/" + name)


def _insert_missing(table_name, **values):
    table = db.metadata.tables[table_name]
    statement = insert(table).values(**values).on_conflict_do_nothing()
    return db.session.execute(statement.returning(*table.primary_key.columns)).first()


def register_seed_commands(app):
    @app.cli.command("db-seed-demo")
    def db_seed_demo():
        """Insert development-only fixtures without changing existing records."""
        required = {
            "alembic_version", "client_sessions", "data_consents", "consent_courses",
            "documents", "grade_goals", "chat_sessions", "chat_messages",
        }
        try:
            if db.engine.dialect.name != "postgresql":
                raise click.ClickException("Demo seed requires PostgreSQL. Configure DATABASE_URL first.")
            if not required.issubset(set(sa.inspect(db.engine).get_table_names())):
                raise click.ClickException(
                    "Database tables are missing. Run `flask --app wsgi:app db upgrade` first."
                )

            now = datetime.now(timezone.utc)
            inserted = 0
            with db.session.begin():
                for label, course, title in (
                    ("student-a", "INT3306", "Demo: Service-oriented architecture"),
                    ("student-b", "INT2204", "Demo: Database fundamentals"),
                ):
                    owner_id = demo_id(label)
                    clients = db.metadata.tables["client_sessions"]
                    exists = db.session.scalar(sa.select(clients.c.id).where(clients.c.id == owner_id))
                    if exists is None:
                        # Tokens are discarded after hashing. Seeded sessions are
                        # fixtures, not usable authentication credentials.
                        token_hash = sha256(secrets.token_urlsafe(32).encode("utf-8")).hexdigest()
                        inserted += bool(_insert_missing(
                            "client_sessions", id=owner_id, token_hash=token_hash,
                            created_at=now, expires_at=now + timedelta(days=30),
                        ))

                    for purpose in ("KNOWLEDGE_QA", "KNOWLEDGE_SEARCH", "DOCUMENT_SUMMARY"):
                        consent_id = demo_id(f"{label}/consent/{purpose}")
                        consent_inserted = _insert_missing(
                            "data_consents", id=consent_id, client_session_id=owner_id,
                            data_category="COURSE_DOCUMENTS", purpose=purpose,
                            is_granted=True, scope_type="SELECTED_COURSES",
                            updated_at=now, granted_at=now,
                        )
                        inserted += bool(consent_inserted)
                        if consent_inserted:
                            # Do not restore courses if someone intentionally
                            # edited an existing consent between seed runs.
                            inserted += bool(_insert_missing(
                                "consent_courses", consent_id=consent_id, course_id=course,
                            ))

                    inserted += bool(_insert_missing(
                        "documents", id=demo_id(f"{label}/document"),
                        client_session_id=owner_id, course_id=course,
                        external_doc_id=f"demo-{label}-notes", title=title,
                        source_revision="demo-v1", index_status="PENDING",
                        is_partial_content=False, created_at=now, updated_at=now,
                    ))
                    inserted += bool(_insert_missing(
                        "grade_goals", id=demo_id(f"{label}/grade-goal"),
                        client_session_id=owner_id, course_id=course,
                        scope_type="COURSE_FINAL", target_score=8, max_scale=10,
                        grading_rule="WEIGHTED_AVERAGE", data_source="MANUAL",
                        updated_at=now,
                    ))
                    chat_id = demo_id(f"{label}/chat")
                    chat_inserted = _insert_missing(
                        "chat_sessions", id=chat_id, client_session_id=owner_id,
                        mode="COURSE_CONTEXT", course_id=course, created_at=now,
                    )
                    inserted += bool(chat_inserted)
                    if chat_inserted:
                        inserted += bool(_insert_missing(
                            "chat_messages", id=demo_id(f"{label}/message"),
                            chat_session_id=chat_id, role="USER", message_type="CHAT",
                            content="Please explain the main ideas in this course.",
                            has_external_knowledge=False, is_partial_content=False,
                            created_at=now,
                        ))
            click.echo(f"Demo seed complete: {inserted} records inserted; existing records unchanged.")
            click.echo(
                "Sessions are development fixtures only; no login tokens are stored or printed. "
                "Documents remain PENDING; no embeddings or AI answers were generated."
            )
        except click.ClickException:
            db.session.rollback()
            raise
        except SQLAlchemyError as error:
            db.session.rollback()
            # Keep connection strings/credentials and raw SQL out of CLI output.
            raise click.ClickException(
                "Demo seed failed and was rolled back. Check PostgreSQL connectivity, "
                "run `flask --app wsgi:app db upgrade`, and retry."
            ) from error
