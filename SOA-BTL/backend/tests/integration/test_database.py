"""Exercise the ERD migration on PostgreSQL, isolated from application data.

Set TEST_DATABASE_URL to a PostgreSQL database whose role can create schemas and
enable pgvector. Each run creates a random schema and removes only that schema.
No application tables are truncated and no database is dropped.
"""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from uuid import uuid4

from flask_migrate import downgrade, upgrade
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from student_assistant import create_app
from student_assistant.extensions import db


TABLE_NAMES = {
    "client_sessions", "data_consents", "consent_courses", "documents",
    "document_access", "document_chunks", "chat_sessions", "chat_messages",
    "chat_citations", "message_documents", "quiz_reviews", "quiz_review_items",
    "knowledge_topics", "grade_goals", "learning_analyses", "learning_evidence",
    "learning_recommendations", "analysis_documents",
}
MIGRATIONS = str(Path(__file__).resolve().parents[2] / "migrations")


def test_all_erd_tables_are_registered():
    # Metadata inspection needs no running database.
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        assert set(db.metadata.tables) == TABLE_NAMES


@pytest.fixture(scope="module")
def database_app():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url and os.environ.get("TEST_DB_HOST"):
        database_url = sa.URL.create(
            "postgresql+psycopg",
            username=os.environ.get("TEST_DB_USER", "ai_student_assistant"),
            password=os.environ.get("TEST_DB_PASSWORD"),
            host=os.environ["TEST_DB_HOST"],
            port=int(os.environ.get("TEST_DB_PORT", "5432")),
            database=os.environ.get("TEST_DB_NAME", "ai_student_assistant"),
        )
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL migration tests")
    url = sa.engine.make_url(database_url)
    if url.get_backend_name() != "postgresql":
        pytest.fail("TEST_DATABASE_URL must point to PostgreSQL with pgvector")

    # This identifier is generated locally and never contains user input.
    schema = "db_test_" + uuid4().hex
    admin = sa.create_engine(url)
    with admin.begin() as connection:
        connection.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
    app = None
    try:
        app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": url,
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"options": f"-csearch_path={schema},public"},
            },
        })
        with app.app_context():
            upgrade(directory=MIGRATIONS)
        yield app, schema
    finally:
        if app is not None:
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        try:
            with admin.begin() as connection:
                connection.execute(sa.text(f'DROP SCHEMA "{schema}" CASCADE'))
        finally:
            admin.dispose()


@pytest.fixture
def connection(database_app):
    app, _ = database_app
    with app.app_context(), db.engine.connect() as connection:
        transaction = connection.begin()
        try:
            yield connection
        finally:
            transaction.rollback()


def insert(connection, table_name, **values):
    table = db.metadata.tables[table_name]
    if "id" in table.c and "id" not in values:
        values["id"] = uuid4()
    connection.execute(table.insert().values(**values))
    return values.get("id")


def owner(connection):
    now = datetime.now(timezone.utc)
    return insert(
        connection, "client_sessions", token_hash=uuid4().hex,
        created_at=now, expires_at=now + timedelta(days=1),
    )


def document_and_chunk(connection, owner_id, course="INT3306"):
    generation = uuid4()
    document_id = insert(
        connection, "documents", client_session_id=owner_id,
        course_id=course, external_doc_id=uuid4().hex, title="SOA course notes",
        index_status="PENDING", is_partial_content=False,
    )
    chunk_id = insert(
        connection, "document_chunks", document_id=document_id,
        index_generation=generation, chunk_index=0,
        content="A service exposes a defined contract.",
        embedding=[0.1, 0.2, 0.3], embedding_model="test-fixture-3d",
    )
    connection.execute(
        db.metadata.tables["documents"].update()
        .where(db.metadata.tables["documents"].c.id == document_id)
        .values(index_status="INDEXED", active_index_generation=generation)
    )
    return document_id, chunk_id


def assistant_message(connection, owner_id, course="INT3306"):
    chat_id = insert(
        connection, "chat_sessions", client_session_id=owner_id,
        mode="COURSE_CONTEXT", course_id=course,
    )
    return insert(
        connection, "chat_messages", chat_session_id=chat_id, role="ASSISTANT",
        message_type="CHAT", content="A service has a contract.",
        answer_status="ANSWERED", has_external_knowledge=False,
        is_partial_content=False,
    )


def assert_rejected(connection, action):
    # A savepoint keeps the enclosing test transaction usable after rejection.
    with pytest.raises(IntegrityError):
        with connection.begin_nested():
            action()


def test_migration_creates_all_tables(connection, database_app):
    _, schema = database_app
    actual = set(sa.inspect(connection).get_table_names(schema=schema))
    assert actual == TABLE_NAMES | {"alembic_version"}
    assert connection.scalar(sa.text("SELECT count(*) FROM pg_extension WHERE extname='vector'")) == 1


def test_vector_values_round_trip(connection):
    _, chunk_id = document_and_chunk(connection, owner(connection))
    chunks = db.metadata.tables["document_chunks"]
    vector = connection.scalar(sa.select(chunks.c.embedding).where(chunks.c.id == chunk_id))
    assert list(vector) == pytest.approx([0.1, 0.2, 0.3])


def test_migration_matches_model_metadata(connection, database_app):
    _, schema = database_app
    context = MigrationContext.configure(connection, opts={
        "compare_type": True, "version_table_schema": schema,
        "include_object": lambda obj, name, kind, reflected, compare_to:
            not (kind == "table" and name == "alembic_version"),
    })
    assert compare_metadata(context, db.metadata) == []


def test_course_final_goal_unique_even_with_null_quiz_group(connection):
    owner_id = owner(connection)
    values = dict(
        client_session_id=owner_id, course_id="INT3306", scope_type="COURSE_FINAL",
        quiz_group_id=None, target_score=8, max_scale=10,
        grading_rule="WEIGHTED_AVERAGE", data_source="MANUAL",
    )
    insert(connection, "grade_goals", **values)
    assert_rejected(connection, lambda: insert(connection, "grade_goals", **values))
    # The same course remains available to a different owner.
    insert(connection, "grade_goals", **{**values, "client_session_id": owner(connection)})


@pytest.mark.parametrize("target", [-1, 11])
def test_grade_goal_rejects_scores_outside_scale(connection, target):
    owner_id = owner(connection)
    assert_rejected(connection, lambda: insert(
        connection, "grade_goals", client_session_id=owner_id, course_id="INT3306",
        scope_type="COURSE_FINAL", target_score=target, max_scale=10,
        grading_rule="WEIGHTED_AVERAGE", data_source="MANUAL",
    ))


@pytest.mark.parametrize("foreign_owner", [False, True], ids=["wrong-course", "wrong-owner"])
def test_message_document_link_enforces_owner_and_course(connection, foreign_owner):
    owner_id = owner(connection)
    other_owner = owner(connection) if foreign_owner else owner_id
    wrong_course = "INT3306" if foreign_owner else "INT2204"
    own_document, _ = document_and_chunk(connection, owner_id)
    foreign_document, _ = document_and_chunk(connection, other_owner, wrong_course)
    message_id = assistant_message(connection, owner_id)
    insert(connection, "message_documents", message_id=message_id,
           document_id=own_document, used_purpose="KNOWLEDGE_QA")
    assert_rejected(connection, lambda: insert(
        connection, "message_documents", message_id=message_id,
        document_id=foreign_document, used_purpose="KNOWLEDGE_QA",
    ))


@pytest.mark.parametrize("foreign_owner", [False, True], ids=["wrong-course", "wrong-owner"])
def test_citation_enforces_owner_and_course(connection, foreign_owner):
    owner_id = owner(connection)
    other_owner = owner(connection) if foreign_owner else owner_id
    wrong_course = "INT3306" if foreign_owner else "INT2204"
    own_document, own_chunk = document_and_chunk(connection, owner_id)
    _, foreign_chunk = document_and_chunk(connection, other_owner, wrong_course)
    message_id = assistant_message(connection, owner_id)
    insert(connection, "message_documents", message_id=message_id,
           document_id=own_document, used_purpose="KNOWLEDGE_QA")
    values = dict(message_id=message_id, quoted_snippet="A service exposes a defined contract.",
                  document_title_snapshot="SOA course notes")
    insert(connection, "chat_citations", chunk_id=own_chunk, **values)
    assert_rejected(connection, lambda: insert(
        connection, "chat_citations", chunk_id=foreign_chunk, **values,
    ))


def test_quiz_question_rejects_points_above_maximum(connection):
    review_id = insert(
        connection, "quiz_reviews", client_session_id=owner(connection),
        course_id="INT3306", external_quiz_id="quiz-1", quiz_title="SOA quiz",
        quiz_status="GRADED", data_source="MANUAL", used_data_categories=[],
        is_complete_attempt=False, has_complete_rubric=False,
        assessment_status="PARTIAL", disclaimer="Reference assessment only.",
    )
    assert_rejected(connection, lambda: insert(
        connection, "quiz_review_items", review_id=review_id, question_number=1,
        question_type="ESSAY", question_text="Define a service.", student_answer="Example",
        official_points=6, max_points=5, explanation="Insufficient detail.",
    ))


def test_learning_recommendation_requires_observed_evidence(connection):
    owner_id = owner(connection)
    analysis_id = insert(
        connection, "learning_analyses", client_session_id=owner_id,
        course_id="INT3306", has_sufficient_data=False,
    )
    topic_id = insert(
        connection, "knowledge_topics", client_session_id=owner_id,
        course_id="INT3306", name="Service contracts",
    )
    assert_rejected(connection, lambda: insert(
        connection, "learning_recommendations", analysis_id=analysis_id,
        topic_id=topic_id, priority_rank=1, weakness_reason="Missing detail",
        study_advice="Review the notes.", observed_evidence=[],
        ai_inference="Possible gap in understanding.",
    ))


def test_selected_consent_and_course_can_be_inserted_in_one_transaction(connection):
    consent_id = insert(
        connection, "data_consents", client_session_id=owner(connection),
        data_category="COURSE_DOCUMENTS", purpose="KNOWLEDGE_QA",
        is_granted=True, scope_type="SELECTED_COURSES",
        granted_at=datetime.now(timezone.utc),
    )
    insert(connection, "consent_courses", consent_id=consent_id, course_id="INT3306")
    # Force commit-time constraint triggers while keeping this test rollback-only.
    connection.execute(sa.text("SET CONSTRAINTS ALL IMMEDIATE"))
    courses = db.metadata.tables["consent_courses"]
    assert connection.scalar(
        sa.select(sa.func.count()).select_from(courses).where(courses.c.consent_id == consent_id)
    ) == 1


def test_selected_consent_requires_a_course_at_transaction_end(connection):
    owner_id = owner(connection)

    def invalid_consent():
        insert(
            connection, "data_consents", client_session_id=owner_id,
            data_category="COURSE_DOCUMENTS", purpose="KNOWLEDGE_QA",
            is_granted=True, scope_type="SELECTED_COURSES",
            granted_at=datetime.now(timezone.utc),
        )
        connection.execute(sa.text("SET CONSTRAINTS ALL IMMEDIATE"))

    assert_rejected(connection, invalid_consent)


def test_all_authorized_consent_must_not_have_course_rows(connection):
    owner_id = owner(connection)

    def invalid_consent():
        consent_id = insert(
            connection, "data_consents", client_session_id=owner_id,
            data_category="COURSE_DOCUMENTS", purpose="KNOWLEDGE_QA",
            is_granted=True, scope_type="ALL_AUTHORIZED_COURSES",
            granted_at=datetime.now(timezone.utc),
        )
        insert(connection, "consent_courses", consent_id=consent_id, course_id="INT3306")
        connection.execute(sa.text("SET CONSTRAINTS ALL IMMEDIATE"))

    assert_rejected(connection, invalid_consent)


def test_indexed_document_requires_chunks_in_its_active_generation(connection):
    owner_id = owner(connection)

    def missing_generation():
        insert(
            connection, "documents", client_session_id=owner_id, course_id="INT3306",
            external_doc_id=uuid4().hex, title="Document without active chunks",
            index_status="INDEXED", active_index_generation=uuid4(),
            is_partial_content=False,
        )
        connection.execute(sa.text("SET CONSTRAINTS ALL IMMEDIATE"))

    assert_rejected(connection, missing_generation)


@pytest.mark.parametrize(
    "embedding, model",
    [([0.4, 0.5], "test-fixture-3d"), ([0.4, 0.5, 0.6], "different-model")],
    ids=["different-dimension", "different-model"],
)
def test_document_generation_rejects_mixed_embedding_configuration(connection, embedding, model):
    document_id, chunk_id = document_and_chunk(connection, owner(connection))
    chunks = db.metadata.tables["document_chunks"]
    generation = connection.scalar(
        sa.select(chunks.c.index_generation).where(chunks.c.id == chunk_id)
    )

    def mixed_generation():
        insert(
            connection, "document_chunks", document_id=document_id,
            index_generation=generation, chunk_index=1, content="Another paragraph.",
            embedding=embedding, embedding_model=model,
        )
        connection.execute(sa.text("SET CONSTRAINTS ALL IMMEDIATE"))

    assert_rejected(connection, mixed_generation)


def test_citation_requires_a_record_of_the_full_source_scope(connection):
    owner_id = owner(connection)
    _, chunk_id = document_and_chunk(connection, owner_id)
    message_id = assistant_message(connection, owner_id)
    # Matching owner and course alone do not replace message_documents.
    assert_rejected(connection, lambda: insert(
        connection, "chat_citations", message_id=message_id, chunk_id=chunk_id,
        quoted_snippet="A service exposes a defined contract.",
        document_title_snapshot="SOA course notes",
    ))


def test_demo_seed_is_repeatable_and_preserves_existing_data(database_app):
    from student_assistant.seed import demo_id

    app, _ = database_app
    runner = app.test_cli_runner()
    first = runner.invoke(args=["db-seed-demo"])
    assert first.exit_code == 0, first.output
    with app.app_context():
        clients = db.metadata.tables["client_sessions"]
        documents = db.metadata.tables["documents"]
        chunks = db.metadata.tables["document_chunks"]
        messages = db.metadata.tables["chat_messages"]
        owners = [demo_id("student-a"), demo_id("student-b")]
        hashes = dict(db.session.execute(
            sa.select(clients.c.id, clients.c.token_hash).where(clients.c.id.in_(owners))
        ).all())
        assert len(hashes) == 2
        assert db.session.scalar(sa.select(sa.func.count()).select_from(chunks)) == 0
        assert db.session.scalar(
            sa.select(sa.func.count()).select_from(messages).where(messages.c.role == "ASSISTANT")
        ) == 0
        db.session.execute(
            documents.update().where(documents.c.id == demo_id("student-a/document"))
            .values(title="Edited after seeding")
        )
        db.session.commit()

    second = runner.invoke(args=["db-seed-demo"])
    assert second.exit_code == 0, second.output
    assert "0 records inserted" in second.output
    with app.app_context():
        assert dict(db.session.execute(
            sa.select(clients.c.id, clients.c.token_hash).where(clients.c.id.in_(owners))
        ).all()) == hashes
        assert db.session.scalar(
            sa.select(documents.c.title).where(documents.c.id == demo_id("student-a/document"))
        ) == "Edited after seeding"
        assert db.session.scalar(
            sa.select(sa.func.count()).select_from(documents).where(documents.c.client_session_id.in_(owners))
        ) == 2
        # Remove only the deterministic fixtures created in this test schema.
        db.session.execute(clients.delete().where(clients.c.id.in_(owners)))
        db.session.commit()


def test_migration_round_trip_in_disposable_schema(database_app):
    app, schema = database_app
    with app.app_context():
        downgrade(directory=MIGRATIONS, revision="base")
        assert set(sa.inspect(db.engine).get_table_names(schema=schema)) <= {"alembic_version"}
        upgrade(directory=MIGRATIONS)
        assert set(sa.inspect(db.engine).get_table_names(schema=schema)) == TABLE_NAMES | {"alembic_version"}
