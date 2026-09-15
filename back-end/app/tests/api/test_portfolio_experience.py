"""Tests públicos de experience/capabilities + idempotencia del seed de experiencia."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.models import (  # noqa: F401
    ProjectModel,
    ExperienceModel,
    UserModel,
    CTFModel,
    WriteupModel,
    AttachmentModel,
    ContactModel,
    FlagSubmissionModel,
    PortfolioProfileModel,
)
from seed_portfolio import SEED_EXPERIENCES, seed_experiences


@pytest.fixture()
def exp_db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'exp.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_seed_experiences_idempotent(exp_db):
    c1, u1 = seed_experiences(exp_db)
    assert c1 == len(SEED_EXPERIENCES)
    assert u1 == 0
    c2, u2 = seed_experiences(exp_db)
    assert c2 == 0
    assert u2 == len(SEED_EXPERIENCES)
    assert exp_db.query(ExperienceModel).count() == len(SEED_EXPERIENCES)


def test_seed_experiences_kinds_and_no_fake_jobs(exp_db):
    seed_experiences(exp_db)
    kinds = {r.kind for r in exp_db.query(ExperienceModel).all()}
    assert kinds <= {"project", "training", "security"}
    # ninguna org inventada tipo empresa empleadora
    for r in exp_db.query(ExperienceModel).all():
        assert r.organization is None


def test_list_experience_public_endpoint(client: TestClient, db):
    # usa fixture client/db del conftest (sqlite app)
    from seed_portfolio import seed_experiences as seed_exp

    seed_exp(db)
    res = client.get("/api/v1/portfolio/experience")
    assert res.status_code == 200
    body = res.json()
    assert "items" in body
    assert len(body["items"]) >= 5
    first = body["items"][0]
    for key in (
        "id",
        "title",
        "kind",
        "start_date",
        "summary",
        "highlights",
        "technologies",
        "links",
        "order",
        "current",
    ):
        assert key in first


def test_capabilities_public_endpoint(client: TestClient):
    res = client.get("/api/v1/portfolio/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert "roles" in body and isinstance(body["roles"], list)
    assert "skills" in body and len(body["skills"]) >= 1
    names = {s["name"] for s in body["skills"]}
    assert "FastAPI" in names
    assert "Angular" in names
    # no inventar cloud/.NET en este endpoint
    assert ".NET" not in names
    assert "Azure" not in names
