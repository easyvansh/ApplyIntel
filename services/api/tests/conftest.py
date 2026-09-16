from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_DATABASE_DIRECTORY = Path(tempfile.mkdtemp(prefix="applyintel-tests-"))
TEST_DATABASE_PATH = TEST_DATABASE_DIRECTORY / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH.as_posix()}"

from database import SessionLocal  # noqa: E402
from main import Application, app, run_database_migrations  # noqa: E402


run_database_migrations()


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    with SessionLocal() as session:
        session.query(Application).delete()
        session.commit()

    yield

    with SessionLocal() as session:
        session.query(Application).delete()
        session.commit()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def application_payload() -> dict[str, str | None]:
    return {
        "company": "Acme Labs",
        "role": "Backend Engineer",
        "location": "Remote",
        "url": "https://example.com/jobs/1",
        "status": "applied",
        "date_applied": "2026-09-16",
        "next_action_date": date.today().isoformat(),
        "notes": "Follow up with the hiring manager.",
    }
