import os
import pathlib

# Ép dùng DB test riêng TRƯỚC khi import app (tránh drop nhầm DB thật)
TEST_DB = pathlib.Path(__file__).parent / "test_kindred.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"
os.environ["GOOGLE_CLIENT_ID"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

PASSWORD = "Password123!"

SURVEY = {
    "age_group": "25-34",
    "situation": "Đi làm văn phòng",
    "recent_feeling": "Căng thẳng",
    "goals": ["Tìm người tâm sự"],
    "topics": ["Công nghệ", "Sách"],
    "activities": ["Đọc sách", "Chạy bộ"],
    "chat_style": "Nhẹ nhàng, chậm rãi",
    "story": "Dạo này công việc áp lực, mình muốn tìm người chia sẻ.",
}


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture()
def client():
    with TestClient(fastapi_app) as c:
        yield c


@pytest.fixture()
def register(client):
    def _register(name: str) -> dict:
        r = client.post(
            "/api/auth/register",
            json={"email": f"{name}@example.com", "username": name, "password": PASSWORD},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        return {
            "id": data["user"]["id"],
            "token": data["access_token"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"},
        }

    return _register


@pytest.fixture()
def befriend(client):
    def _befriend(a: dict, b: dict) -> int:
        r = client.post(f"/api/connections/request/{b['id']}", headers=a["headers"])
        assert r.status_code == 201, r.text
        cid = r.json()["connection_id"]
        r = client.put(f"/api/connections/{cid}/accept", headers=b["headers"])
        assert r.status_code == 200, r.text
        return cid

    return _befriend


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    TEST_DB.unlink(missing_ok=True)
