"""
Integridad de solved vs solved_count en POST /ctfs/{id}/submit y PUT.

solved / solved_at: solo el owner (admin).
solved_count: solo aciertos de visitantes, deduplicados por user_id o por IP
anónima. Un anónimo sin IP no incrementa el contador.
"""

import hashlib
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..conftest import _auth_headers
from ...infrastructure.persistence.models.ctf_model import CTFModel
from ...infrastructure.persistence.models.flag_submission_model import FlagSubmissionModel

FLAG = "flag{test}"


def _insert_ctf(db: Session, *, title: str = "Public CTF") -> str:
    cid = str(uuid4())
    db.add(
        CTFModel(
            id=cid,
            title=title,
            level="easy",
            category="web",
            platform="HackTheBox",
            description="public challenge",
            points=100,
            hints=json.dumps(["a hint"]),
            skills=json.dumps(["web"]),
            flag_hash=hashlib.sha256(FLAG.encode()).hexdigest(),
            is_flag_regex=False,
            status="published",
            is_active=True,
            solved=False,
            solved_count=0,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    return cid


def _public_ctf(client: TestClient, cid: str) -> dict:
    response = client.get(f"/api/v1/ctfs/{cid}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "flag_hash" not in body
    assert "flagHash" not in body
    assert FLAG not in response.text
    return body


def _submit(client: TestClient, cid: str, headers: Optional[dict] = None, flag: str = FLAG):
    response = client.post(
        f"/api/v1/ctfs/{cid}/submit",
        json={"flag": flag},
        headers=headers or {},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert FLAG not in response.text
    assert "flag_hash" not in body
    return body


@contextmanager
def _peer(client: TestClient, host: Optional[str]) -> Iterator[TestClient]:
    """Force the ASGI client address seen by POST /submit. host=None means no IP."""
    transport = client._transport
    original = transport.app

    async def _app(scope, receive, send):
        if scope["type"] == "http":
            scope = dict(scope)
            scope["client"] = None if host is None else [host, 50000]
        await original(scope, receive, send)

    transport.app = _app
    try:
        yield client
    finally:
        transport.app = original


class TestVisitorSubmitDoesNotSolve:
    def test_anonymous_correct_does_not_mark_solved(self, client: TestClient, db: Session):
        cid = _insert_ctf(db)
        body = _submit(client, cid)
        assert body["success"] is True
        assert body["is_correct"] is True

        state = _public_ctf(client, cid)
        assert state["solved"] is False
        assert state["solved_at"] is None
        assert state["solved_count"] == 1

    def test_non_admin_user_correct_does_not_mark_solved(
        self, client: TestClient, db: Session, user_headers: dict
    ):
        cid = _insert_ctf(db)
        body = _submit(client, cid, user_headers)
        assert body["is_correct"] is True

        state = _public_ctf(client, cid)
        assert state["solved"] is False
        assert state["solved_at"] is None
        assert state["solved_count"] == 1

    def test_wrong_flag_does_not_mark_or_count(self, client: TestClient, db: Session):
        cid = _insert_ctf(db)
        body = _submit(client, cid, flag="flag{wrong}")
        assert body["success"] is False
        assert body["is_correct"] is False

        state = _public_ctf(client, cid)
        assert state["solved"] is False
        assert state["solved_count"] == 0


class TestAdminSubmitMarksSolvedWithoutCounting:
    def test_admin_correct_sets_solved_and_skips_counter(
        self, client: TestClient, db: Session, admin_headers: dict
    ):
        cid = _insert_ctf(db)
        body = _submit(client, cid, admin_headers)
        assert body["success"] is True
        assert body["is_correct"] is True

        state = _public_ctf(client, cid)
        assert state["solved"] is True
        assert state["solved_at"] is not None
        assert state["solved_count"] == 0

    def test_visitor_after_admin_increments_without_clearing_solved(
        self, client: TestClient, db: Session, admin_headers: dict
    ):
        cid = _insert_ctf(db)
        _submit(client, cid, admin_headers)
        visitor = _submit(client, cid)
        assert visitor["is_correct"] is True

        state = _public_ctf(client, cid)
        assert state["solved"] is True
        assert state["solved_count"] == 1


class TestSolvedCountDedupe:
    def test_second_correct_from_same_user_does_not_increment(
        self, client: TestClient, db: Session, user_headers: dict
    ):
        cid = _insert_ctf(db)
        first = _submit(client, cid, user_headers)
        assert first["is_correct"] is True
        assert _public_ctf(client, cid)["solved_count"] == 1

        second = _submit(client, cid, user_headers)
        assert second["is_correct"] is False
        state = _public_ctf(client, cid)
        assert state["solved"] is False
        assert state["solved_count"] == 1

        other_headers = _auth_headers(
            db, email="other@example.com", username="othervisitor", is_admin=False
        )
        other = _submit(client, cid, other_headers)
        assert other["is_correct"] is True
        state = _public_ctf(client, cid)
        assert state["solved"] is False
        assert state["solved_count"] == 2

    def test_second_anonymous_from_same_ip_does_not_increment(
        self, client: TestClient, db: Session
    ):
        cid = _insert_ctf(db)
        first = _submit(client, cid)
        second = _submit(client, cid)
        assert first["is_correct"] is True
        assert second["is_correct"] is True

        state = _public_ctf(client, cid)
        assert state["solved"] is False
        assert state["solved_at"] is None
        assert state["solved_count"] == 1

        db.expire_all()
        stored = (
            db.query(FlagSubmissionModel)
            .filter(FlagSubmissionModel.ctf_id == cid, FlagSubmissionModel.is_correct == True)
            .all()
        )
        assert len(stored) == 2
        assert all(row.flag != FLAG for row in stored)

    def test_distinct_anonymous_ips_each_increment_once(
        self, client: TestClient, db: Session
    ):
        cid = _insert_ctf(db)
        with _peer(client, "203.0.113.10") as peer_a:
            assert _submit(peer_a, cid)["is_correct"] is True
            assert _submit(peer_a, cid)["is_correct"] is True
        with _peer(client, "203.0.113.20") as peer_b:
            assert _submit(peer_b, cid)["is_correct"] is True

        state = _public_ctf(client, cid)
        assert state["solved"] is False
        assert state["solved_count"] == 2

    def test_anonymous_without_ip_does_not_increment(
        self, client: TestClient, db: Session
    ):
        cid = _insert_ctf(db)
        with _peer(client, None) as bare:
            first = _submit(bare, cid)
            second = _submit(bare, cid)
        assert first["is_correct"] is True
        assert second["is_correct"] is True

        state = _public_ctf(client, cid)
        assert state["solved"] is False
        assert state["solved_at"] is None
        assert state["solved_count"] == 0


class TestAdminPutSolvedFlag:
    def test_put_true_marks_solved_without_touching_counter(
        self, client: TestClient, db: Session, admin_headers: dict
    ):
        cid = _insert_ctf(db)
        _submit(client, cid)
        assert _public_ctf(client, cid)["solved_count"] == 1

        response = client.put(
            f"/api/v1/ctfs/{cid}",
            json={"solved": True},
            headers=admin_headers,
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert FLAG not in response.text
        assert "flag_hash" not in body
        assert body["solved"] is True
        assert body["solved_at"] is not None
        assert body["solved_count"] == 1

    def test_put_false_clears_mark_and_keeps_counter(
        self, client: TestClient, db: Session, admin_headers: dict, user_headers: dict
    ):
        cid = _insert_ctf(db)
        marked = client.put(
            f"/api/v1/ctfs/{cid}",
            json={"solved": True},
            headers=admin_headers,
        )
        assert marked.status_code == 200
        assert marked.json()["solved"] is True

        _submit(client, cid)
        before = _public_ctf(client, cid)
        assert before["solved_count"] == 1

        cleared = client.put(
            f"/api/v1/ctfs/{cid}",
            json={"solved": False},
            headers=admin_headers,
        )
        assert cleared.status_code == 200, cleared.text
        body = cleared.json()
        assert body["solved"] is False
        assert body["solved_at"] is None
        assert body["solved_count"] == 1
        assert FLAG not in cleared.text

        forbidden = client.put(
            f"/api/v1/ctfs/{cid}",
            json={"solved": True},
            headers=user_headers,
        )
        assert forbidden.status_code == 403
        after = _public_ctf(client, cid)
        assert after["solved"] is False
        assert after["solved_at"] is None
        assert after["solved_count"] == 1


def test_solved_semantics_revision_is_head_and_noop():
    """Nueva revisión sobre el head: sin columnas y sin reescritura de filas."""
    import importlib.util

    from alembic.config import Config
    from alembic.script import ScriptDirectory

    backend_root = Path(__file__).resolve().parents[3]
    revision_path = (
        backend_root / "alembic" / "versions" / "c8a41e0b7d22_preserve_ctf_solved_semantics.py"
    )
    spec = importlib.util.spec_from_file_location("ctf_solved_revision", revision_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "c8a41e0b7d22"
    assert module.down_revision == "b7e4a1c290fd"
    module.upgrade()
    module.downgrade()

    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["c8a41e0b7d22"]
