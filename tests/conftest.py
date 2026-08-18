import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash


_TEMP_PATH = Path(tempfile.mkdtemp(prefix="interntrack-tests-"))
_DATABASE_PATH = _TEMP_PATH / "test.db"

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ADZUNA_APP_ID", "test-app-id")
os.environ.setdefault("ADZUNA_APP_KEY", "test-app-key")
os.environ["DATABASE_URL"] = f"sqlite:///{_DATABASE_PATH.as_posix()}"
os.environ["SESSION_FILE_DIR"] = str(_TEMP_PATH / "sessions")

with sqlite3.connect(_DATABASE_PATH) as connection:
    schema_path = Path(__file__).parents[1] / "schema.sql"
    connection.executescript(schema_path.read_text(encoding="utf-8"))

import app as app_module  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    app_module.db._disconnect()
    app_module.db._engine.dispose()
    shutil.rmtree(_TEMP_PATH, ignore_errors=True)


@pytest.fixture(autouse=True)
def block_real_adzuna_requests(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Tests must not make real Adzuna HTTP requests")

    monkeypatch.setattr("jobs.requests.get", fail_if_called)


@pytest.fixture(autouse=True)
def clean_database():
    with sqlite3.connect(_DATABASE_PATH) as connection:
        connection.execute("DELETE FROM applications")
        connection.execute("DELETE FROM users")
    yield


@pytest.fixture
def app():
    app_module.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    yield app_module.app
    app_module.app.config["WTF_CSRF_ENABLED"] = False


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def database():
    connection = sqlite3.connect(_DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def create_user(database):
    def create(username="alice", password="password123"):
        cursor = database.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        database.commit()
        return cursor.lastrowid

    return create


@pytest.fixture
def logged_in_client(client, create_user):
    user_id = create_user()
    with client.session_transaction() as flask_session:
        flask_session["user_id"] = user_id
    return client, user_id


@pytest.fixture
def create_application(database):
    def create(user_id, external_id="job-1"):
        cursor = database.execute(
            """
            INSERT INTO applications
                (user_id, external_id, title, company, location, apply_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                external_id,
                "Software Intern",
                "Example Corp",
                "Remote",
                "https://example.com/jobs/1",
            ),
        )
        database.commit()
        return cursor.lastrowid

    return create
