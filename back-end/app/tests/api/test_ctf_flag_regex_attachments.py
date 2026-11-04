"""
Persistencia de flags regex y adjuntos URL.

- is_flag_regex debe guardarse y leerse en CTFSqlRepository (crear y actualizar).
- flag_hash debe admitir patrones regex más largos que un SHA-256 (64).
- POST /attachments/url debe crear el adjunto (antes: 500 por kwarg inválido).
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ...infrastructure.persistence.models.attachment_model import AttachmentModel
from ...infrastructure.persistence.models.ctf_model import CTFModel

REGEX_FLAG = r"^flag\{regex_[0-9]{3}\}$"


def _create_ctf(client: TestClient, headers: dict, **overrides) -> str:
    payload = {
        "title": "Regex CTF",
        "level": "easy",
        "category": "web",
        "platform": "Custom",
        "description": "reto de prueba",
        "points": 100,
        "flag": "flag{static}",
    }
    payload.update(overrides)
    response = client.post("/api/v1/ctfs", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _ensure_published(client: TestClient, headers: dict, cid: str) -> None:
    current = client.get(f"/api/v1/ctfs/{cid}", headers=headers).json()
    if current["status"] != "published":
        response = client.post(f"/api/v1/ctfs/{cid}/publish", headers=headers)
        assert response.status_code == 200, response.text


def _submit(client: TestClient, cid: str, flag: str) -> dict:
    response = client.post(f"/api/v1/ctfs/{cid}/submit", json={"flag": flag})
    assert response.status_code == 200, response.text
    return response.json()


def test_create_regex_flag_persists_and_matches(client: TestClient, db: Session, admin_headers: dict):
    cid = _create_ctf(client, admin_headers, flag=REGEX_FLAG, is_flag_regex=True)

    model = db.query(CTFModel).filter(CTFModel.id == cid).first()
    db.refresh(model)
    assert model.is_flag_regex is True
    assert model.flag_hash == REGEX_FLAG

    _ensure_published(client, admin_headers, cid)
    assert _submit(client, cid, "flag{regex_123}")["success"] is True
    assert _submit(client, cid, "flag{regex_12}")["success"] is False


def test_update_static_to_regex_persists(client: TestClient, db: Session, admin_headers: dict):
    cid = _create_ctf(client, admin_headers)
    response = client.put(
        f"/api/v1/ctfs/{cid}",
        json={"flag": REGEX_FLAG, "is_flag_regex": True},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text

    model = db.query(CTFModel).filter(CTFModel.id == cid).first()
    db.refresh(model)
    assert model.is_flag_regex is True

    _ensure_published(client, admin_headers, cid)
    assert _submit(client, cid, "flag{regex_007}")["success"] is True
    assert _submit(client, cid, "flag{static}")["success"] is False


def test_update_regex_back_to_static(client: TestClient, db: Session, admin_headers: dict):
    cid = _create_ctf(client, admin_headers, flag=REGEX_FLAG, is_flag_regex=True)
    response = client.put(
        f"/api/v1/ctfs/{cid}",
        json={"flag": "flag{otra}", "is_flag_regex": False},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text

    _ensure_published(client, admin_headers, cid)
    assert _submit(client, cid, "flag{otra}")["success"] is True
    assert _submit(client, cid, "flag{regex_123}")["success"] is False


def test_flag_hash_column_fits_long_regex():
    length = CTFModel.__table__.c.flag_hash.type.length
    assert length is None or length >= 500


def test_add_url_attachment(client: TestClient, db: Session, admin_headers: dict):
    cid = _create_ctf(client, admin_headers)
    response = client.post(
        "/api/v1/attachments/url",
        json={
            "filename": "Instancia del reto",
            "attachment_type": "url",
            "ctf_id": cid,
            "url": "https://ctf.example.org/instancia",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["filename"] == "Instancia del reto"
    assert body["attachment_type"] == "url"
    assert body["ctf_id"] == cid

    stored = db.query(AttachmentModel).filter(AttachmentModel.ctf_id == cid).all()
    assert [a.name for a in stored] == ["Instancia del reto"]


def test_add_url_attachment_requires_admin(client: TestClient, user_headers: dict, admin_headers: dict):
    cid = _create_ctf(client, admin_headers)
    response = client.post(
        "/api/v1/attachments/url",
        json={"attachment_type": "url", "ctf_id": cid, "url": "https://ctf.example.org/x"},
        headers=user_headers,
    )
    assert response.status_code == 403


def test_update_invalid_regex_returns_400(client: TestClient, admin_headers: dict):
    cid = _create_ctf(client, admin_headers)
    response = client.put(
        f"/api/v1/ctfs/{cid}",
        json={"flag": "flag{(", "is_flag_regex": True},
        headers=admin_headers,
    )
    assert response.status_code == 400, response.text


def test_regex_pattern_too_long_returns_400(client: TestClient, admin_headers: dict):
    response = client.post(
        "/api/v1/ctfs",
        json={
            "title": "Regex largo",
            "level": "easy",
            "category": "web",
            "points": 100,
            "flag": "^flag\\{" + "a" * 600 + "\\}$",
            "is_flag_regex": True,
        },
        headers=admin_headers,
    )
    assert response.status_code == 400, response.text


def test_add_url_attachment_rejects_file_type_and_unknown_ctf(client: TestClient, admin_headers: dict):
    cid = _create_ctf(client, admin_headers)
    as_file = client.post(
        "/api/v1/attachments/url",
        json={"attachment_type": "file", "ctf_id": cid, "url": "https://ctf.example.org/x"},
        headers=admin_headers,
    )
    assert as_file.status_code == 422

    missing = client.post(
        "/api/v1/attachments/url",
        json={
            "attachment_type": "url",
            "ctf_id": "00000000-0000-0000-0000-000000000000",
            "url": "https://ctf.example.org/x",
        },
        headers=admin_headers,
    )
    assert missing.status_code == 404
