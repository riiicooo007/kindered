from app.core.security import create_access_token
from tests.conftest import PASSWORD


def test_register_and_me(client, register):
    u = register("alice")
    r = client.get("/api/users/me", headers=u["headers"])
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "alice"
    assert body["has_completed_survey"] is False


def test_register_duplicate_email_or_username(client, register):
    register("alice")
    r = client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "username": "other", "password": PASSWORD},
    )
    assert r.status_code == 409
    r = client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "username": "ALICE", "password": PASSWORD},
    )
    assert r.status_code == 409


def test_register_validation(client):
    r = client.post("/api/auth/register", json={"email": "bad", "username": "ab", "password": "short"})
    assert r.status_code == 422


def test_login_with_email_and_username(client, register):
    register("alice")
    for ident in ("alice", "alice@example.com", "ALICE"):
        r = client.post("/api/auth/login", json={"identifier": ident, "password": PASSWORD})
        assert r.status_code == 200, ident
        assert r.json()["access_token"]


def test_login_wrong_password(client, register):
    register("alice")
    r = client.post("/api/auth/login", json={"identifier": "alice", "password": "wrong-password"})
    assert r.status_code == 401


def test_protected_routes_need_token(client):
    assert client.get("/api/users/me").status_code == 401
    assert client.get("/api/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_expired_token_rejected(client, register):
    u = register("alice")
    expired = create_access_token(u["id"], expires_minutes=-1)
    r = client.get("/api/users/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401
    assert "hết hạn" in r.json()["detail"]


def test_google_login_not_configured(client):
    r = client.post("/api/auth/google", json={"id_token": "x" * 20})
    assert r.status_code == 503


def test_public_profile_hides_private_data(client, register):
    a, b = register("alice"), register("bob")
    r = client.get(f"/api/users/{b['id']}", headers=a["headers"])
    assert r.status_code == 200
    assert "email" not in r.json()
    assert client.get("/api/users/99999", headers=a["headers"]).status_code == 404


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
