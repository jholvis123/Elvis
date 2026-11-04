"""
Tablero estilo CTFd: jugadores con alias, pistas con coste, ranking,
resoluciones por reto y tablero por categoría.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ...core.config import settings
from ...infrastructure.persistence.models.ctf_model import CTFModel
from ...infrastructure.persistence.models.flag_submission_model import FlagSubmissionModel
from ...infrastructure.persistence.models.user_model import UserModel

PASSWORD = "jugador-123"


@pytest.fixture
def players_enabled():
    previous = settings.ALLOW_PLAYER_REGISTER
    settings.ALLOW_PLAYER_REGISTER = True
    yield
    settings.ALLOW_PLAYER_REGISTER = previous


def _register(client: TestClient, alias: str):
    return client.post(
        "/api/v1/auth/register-player",
        json={"username": alias, "password": PASSWORD},
    )


def _player(client: TestClient, alias: str) -> dict:
    assert _register(client, alias).status_code == 201
    response = client.post(
        "/api/v1/auth/login",
        json={"username": alias, "password": PASSWORD, "token_in_body": True},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _ctf(client: TestClient, admin_headers: dict, **overrides) -> str:
    payload = {
        "title": "Web 100",
        "level": "easy",
        "category": "web",
        "platform": "Custom",
        "points": 100,
        "flag": "flag{ok}",
    }
    payload.update(overrides)
    response = client.post("/api/v1/ctfs", json=payload, headers=admin_headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _solve(client: TestClient, cid: str, headers: dict, flag: str = "flag{ok}") -> dict:
    response = client.post(f"/api/v1/ctfs/{cid}/submit", json={"flag": flag}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------- registro


class TestPlayerRegister:
    def test_disabled_by_default(self, client: TestClient):
        assert settings.ALLOW_PLAYER_REGISTER is False
        response = _register(client, "jugador1")
        assert response.status_code == 403

    def test_register_without_email_is_never_admin(
        self, client: TestClient, db: Session, players_enabled
    ):
        response = client.post(
            "/api/v1/auth/register-player",
            json={"username": "neo", "password": PASSWORD, "is_admin": True},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["username"] == "neo"
        assert body["email"] is None
        assert body["is_admin"] is False
        stored = db.query(UserModel).filter(UserModel.username == "neo").one()
        assert stored.is_admin is False
        assert stored.email is None

    def test_several_players_without_email(self, client: TestClient, players_enabled):
        assert _register(client, "trinity").status_code == 201
        assert _register(client, "morpheus").status_code == 201

    @pytest.mark.parametrize("alias", ["ab", "con espacio", "x" * 31, "<script>", "Admin", "ELVIS"])
    def test_invalid_or_reserved_alias(self, client: TestClient, players_enabled, alias: str):
        assert _register(client, alias).status_code == 422

    def test_alias_unique_case_insensitive(self, client: TestClient, players_enabled):
        assert _register(client, "Cypher").status_code == 201
        response = _register(client, "cypher")
        assert response.status_code == 400

    def test_short_password_rejected(self, client: TestClient, players_enabled):
        response = client.post(
            "/api/v1/auth/register-player", json={"username": "tank", "password": "corta"}
        )
        assert response.status_code == 422

    def test_login_by_alias_and_wrong_password(self, client: TestClient, players_enabled):
        assert _register(client, "switch").status_code == 201
        ok = client.post("/api/v1/auth/login", json={"username": "SWITCH", "password": PASSWORD})
        assert ok.status_code == 200
        bad = client.post("/api/v1/auth/login", json={"username": "switch", "password": "nope-nope"})
        assert bad.status_code == 401
        missing = client.post("/api/v1/auth/login", json={"password": PASSWORD})
        assert missing.status_code == 422

    def test_player_cannot_use_admin_endpoints(
        self, client: TestClient, players_enabled, admin_headers: dict
    ):
        player = _player(client, "mouse")
        cid = _ctf(client, admin_headers)
        assert client.get("/api/v1/ctfs/admin/all", headers=player).status_code == 403
        assert client.put(f"/api/v1/ctfs/{cid}", json={"points": 1}, headers=player).status_code == 403


# ---------------------------------------------------------------- pistas


class TestHints:
    def _paid_ctf(self, client, admin_headers) -> str:
        return _ctf(
            client,
            admin_headers,
            hints=["pista gratis", "pista de pago"],
            hint_costs=[0, 50],
        )

    def test_paid_hint_hidden_until_unlocked(
        self, client: TestClient, players_enabled, admin_headers: dict
    ):
        cid = self._paid_ctf(client, admin_headers)

        anon = client.get(f"/api/v1/ctfs/{cid}").json()
        assert anon["hints"] == ["pista gratis", None]
        assert anon["hint_costs"] == [0, 50]
        assert anon["unlocked_hints"] == [0]
        assert "pista de pago" not in client.get("/api/v1/ctfs").text

        admin_view = client.get(f"/api/v1/ctfs/{cid}", headers=admin_headers).json()
        assert admin_view["hints"] == ["pista gratis", "pista de pago"]

        player = _player(client, "oracle")
        first = client.post(f"/api/v1/ctfs/{cid}/hints/1/unlock", headers=player)
        assert first.status_code == 200, first.text
        assert first.json() == {
            "index": 1,
            "hint": "pista de pago",
            "cost": 50,
            "already_unlocked": False,
        }
        again = client.post(f"/api/v1/ctfs/{cid}/hints/1/unlock", headers=player).json()
        assert again["already_unlocked"] is True

        mine = client.get(f"/api/v1/ctfs/{cid}", headers=player).json()
        assert mine["hints"] == ["pista gratis", "pista de pago"]
        assert mine["unlocked_hints"] == [0, 1]

    def test_unlock_requires_login_and_valid_index(
        self, client: TestClient, players_enabled, admin_headers: dict
    ):
        cid = self._paid_ctf(client, admin_headers)
        assert client.post(f"/api/v1/ctfs/{cid}/hints/1/unlock").status_code == 401
        player = _player(client, "apoc")
        assert client.post(f"/api/v1/ctfs/{cid}/hints/5/unlock", headers=player).status_code == 404

    def test_unlock_on_draft_is_404(
        self, client: TestClient, db: Session, players_enabled, admin_headers: dict
    ):
        cid = self._paid_ctf(client, admin_headers)
        db.query(CTFModel).filter(CTFModel.id == cid).update({"status": "draft"})
        db.commit()
        player = _player(client, "dozer")
        assert client.post(f"/api/v1/ctfs/{cid}/hints/1/unlock", headers=player).status_code == 404

    def test_hint_costs_validated_and_aligned(self, client: TestClient, admin_headers: dict):
        bad = client.post(
            "/api/v1/ctfs",
            json={"title": "x" * 5, "level": "easy", "category": "web", "hints": ["a"], "hint_costs": [-1]},
            headers=admin_headers,
        )
        assert bad.status_code == 422
        cid = _ctf(client, admin_headers, hints=["a", "b", "c"], hint_costs=[10])
        body = client.get(f"/api/v1/ctfs/{cid}", headers=admin_headers).json()
        assert body["hint_costs"] == [10, 0, 0]
        updated = client.put(
            f"/api/v1/ctfs/{cid}", json={"hints": ["a"]}, headers=admin_headers
        ).json()
        assert updated["hint_costs"] == [10]


# ---------------------------------------------------------------- ranking


class TestScoreboard:
    def test_ranking_excludes_admin_and_subtracts_hints(
        self, client: TestClient, players_enabled, admin_headers: dict
    ):
        cid = _ctf(client, admin_headers, points=200, hints=["h"], hint_costs=[30])
        alice = _player(client, "alice")
        bob = _player(client, "bob")

        assert _solve(client, cid, alice)["success"] is True
        assert _solve(client, cid, bob)["success"] is True
        _solve(client, cid, admin_headers)
        client.post(f"/api/v1/ctfs/{cid}/hints/0/unlock", headers=alice)

        board = client.get("/api/v1/ctfs/leaderboard/top").json()
        assert board["total_players"] == 2
        assert [(e["username"], e["total_points"], e["hint_penalty"]) for e in board["entries"]] == [
            ("bob", 200, 0),
            ("alice", 170, 30),
        ]

        me = client.get("/api/v1/ctfs/leaderboard/me", headers=alice).json()
        assert me["total_points"] == 170
        assert me["rank"] == 2

    def test_tie_goes_to_earliest_solver(
        self, client: TestClient, db: Session, players_enabled, admin_headers: dict
    ):
        cid = _ctf(client, admin_headers)
        early = _player(client, "early")
        late = _player(client, "late")
        _solve(client, cid, late)
        _solve(client, cid, early)
        # Forzar el orden temporal: "early" resolvió una hora antes
        early_id = db.query(UserModel).filter(UserModel.username == "early").one().id
        db.query(FlagSubmissionModel).filter(FlagSubmissionModel.user_id == early_id).update(
            {"submitted_at": datetime.utcnow() - timedelta(hours=1)}
        )
        db.commit()

        entries = client.get("/api/v1/ctfs/leaderboard/top").json()["entries"]
        assert [e["username"] for e in entries] == ["early", "late"]

        solves = client.get(f"/api/v1/ctfs/{cid}/solves").json()
        assert solves["total"] == 2
        assert [(s["username"], s["first_blood"]) for s in solves["items"]] == [
            ("early", True),
            ("late", False),
        ]

    def test_unpublished_ctf_does_not_score(
        self, client: TestClient, db: Session, players_enabled, admin_headers: dict
    ):
        cid = _ctf(client, admin_headers)
        player = _player(client, "ghost")
        _solve(client, cid, player)
        db.query(CTFModel).filter(CTFModel.id == cid).update({"status": "archived"})
        db.commit()
        assert client.get("/api/v1/ctfs/leaderboard/top").json()["total_players"] == 0
        assert client.get(f"/api/v1/ctfs/{cid}/solves").status_code == 404


# ---------------------------------------------------------------- tablero


class TestBoard:
    def test_board_groups_by_category_and_marks_mine(
        self, client: TestClient, players_enabled, admin_headers: dict
    ):
        web = _ctf(client, admin_headers, title="Web 100", points=100)
        _ctf(client, admin_headers, title="Web 300", points=300)
        _ctf(client, admin_headers, title="Cripto 200", category="crypto", points=200)
        _ctf(client, admin_headers, title="Borrador", is_active=False)

        anon = client.get("/api/v1/ctfs/board").json()
        assert anon["total"] == 3
        assert anon["my_score"] is None
        cats = {c["category"]: [x["title"] for x in c["challenges"]] for c in anon["categories"]}
        assert cats == {"crypto": ["Cripto 200"], "web": ["Web 100", "Web 300"]}

        player = _player(client, "zion")
        _solve(client, web, player)
        mine = client.get("/api/v1/ctfs/board", headers=player).json()
        assert mine["solved_by_me"] == 1
        assert mine["my_score"] == 100
        assert mine["my_rank"] == 1
        web_tiles = next(c for c in mine["categories"] if c["category"] == "web")["challenges"]
        assert [(t["title"], t["solved_by_me"], t["solves"]) for t in web_tiles] == [
            ("Web 100", True, 1),
            ("Web 300", False, 0),
        ]
