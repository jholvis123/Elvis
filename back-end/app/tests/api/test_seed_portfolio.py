"""Tests del seed de portafolio: idempotencia y sin duplicados por github_url."""

import json
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.models import (  # noqa: F401
    ProjectModel,
    UserModel,
    CTFModel,
    WriteupModel,
    AttachmentModel,
    ContactModel,
    FlagSubmissionModel,
    PortfolioProfileModel,
)
from seed_portfolio import SEED_PROJECTS, seed_projects


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "seed_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
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


def test_seed_creates_published_projects(db_session):
    created, updated = seed_projects(db_session)
    assert created == len(SEED_PROJECTS)
    assert updated == 0
    rows = db_session.query(ProjectModel).all()
    assert len(rows) == len(SEED_PROJECTS)
    assert all(r.status == "published" for r in rows)
    urls = {r.github_url for r in rows}
    assert "https://github.com/jholvis123/Elvis" in urls
    assert "https://github.com/jholvis123/CTFd" in urls


def test_seed_is_idempotent_by_github_url(db_session):
    seed_projects(db_session)
    created, updated = seed_projects(db_session)
    assert created == 0
    assert updated == len(SEED_PROJECTS)
    assert db_session.query(ProjectModel).count() == len(SEED_PROJECTS)


def test_seed_does_not_invent_ctf_or_writeup_rows(db_session):
    seed_projects(db_session)
    assert db_session.query(CTFModel).count() == 0
    assert db_session.query(WriteupModel).count() == 0


def test_featured_flags_match_seed_definition(db_session):
    seed_projects(db_session)
    by_url = {
        r.github_url: r
        for r in db_session.query(ProjectModel).all()
    }
    for item in SEED_PROJECTS:
        row = by_url[item["github_url"]]
        assert row.featured is bool(item["featured"])
        assert json.loads(row.technologies) == item["technologies"]
