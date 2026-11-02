from app.services.matching_service import UserFeatures, build_text, compute_matches
from tests.conftest import SURVEY


def _f(uid, **kw):
    base = dict(
        age_group="25-34", situation="Đi làm văn phòng", topics=["Công nghệ", "Sách"], activities=["Đọc sách"],
        goals=["Tìm người tâm sự"], chat_style="Nhẹ nhàng", story="", bio="",
    )
    base.update(kw)
    return UserFeatures(user_id=uid, **base)


def test_build_text_has_semantic_prefixes():
    text = build_text(_f(1))
    assert "độ_tuổi_25_34" in text
    assert "hoàn_cảnh_đi_làm_văn_phòng" in text
    assert "chủ_đề_công_nghệ" in text


def test_self_excluded_sorted_and_bounded():
    feats = [
        _f(1),
        _f(2),  # giống hệt
        _f(3, age_group="45+", situation="Sinh viên", topics=["Du lịch"], activities=["Leo núi"], goals=["Học hỏi"]),
    ]
    res = compute_matches(feats, me_id=1)
    assert [r.user_id for r in res] == [2, 3]
    assert all(0 <= r.score <= 100 for r in res)
    assert res[0].score > res[1].score
    assert res[0].score == 100.0


def test_common_interests_and_reasons():
    feats = [_f(1, topics=["Công nghệ", "Sách"]), _f(2, topics=["sách", "Du lịch"], activities=[])]
    res = compute_matches(feats, me_id=1)[0]
    assert "Sách" in res.common_interests
    assert any("Cùng quan tâm" in r for r in res.reasons)


def test_needs_at_least_two_users():
    assert compute_matches([_f(1)], me_id=1) == []
    assert compute_matches([_f(1), _f(2)], me_id=99) == []


def test_api_suggestions_flow(client, register):
    a, b, c = register("alice"), register("bob"), register("carol")

    # chưa làm khảo sát -> 400
    assert client.get("/api/matching/suggestions", headers=a["headers"]).status_code == 400

    assert client.post("/api/survey", json=SURVEY, headers=a["headers"]).status_code == 200
    client.post("/api/survey", json=SURVEY, headers=b["headers"])
    far = dict(SURVEY, age_group="45+", situation="Sinh viên", topics=["Du lịch"], activities=["Leo núi"], goals=["Học hỏi kỹ năng"])
    client.post("/api/survey", json=far, headers=c["headers"])

    r = client.get("/api/matching/suggestions", headers=a["headers"])
    assert r.status_code == 200
    data = r.json()
    assert [x["user"]["id"] for x in data] == [b["id"], c["id"]]  # bob giống hơn, không có chính mình
    assert data[0]["score"] > data[1]["score"]
    assert "email" not in data[0]["user"]

    # bộ lọc
    r = client.get("/api/matching/suggestions", params={"age_group": "45+"}, headers=a["headers"])
    assert [x["user"]["id"] for x in r.json()] == [c["id"]]
    r = client.get("/api/matching/suggestions", params={"interest": "sách"}, headers=a["headers"])
    assert [x["user"]["id"] for x in r.json()] == [b["id"]]


def test_survey_syncs_profile_and_is_retrievable(client, register):
    a = register("alice")
    client.post("/api/survey", json=SURVEY, headers=a["headers"])
    prof = client.get("/api/profile/me", headers=a["headers"]).json()
    assert prof["age_group"] == "25-34"
    assert set(prof["interests"]) >= {"Công nghệ", "Đọc sách"}
    assert client.get("/api/survey/me", headers=a["headers"]).json()["story"] == SURVEY["story"]
    assert client.get("/api/users/me", headers=a["headers"]).json()["has_completed_survey"] is True


def test_profile_update(client, register):
    a = register("alice")
    r = client.put("/api/profile/me", json={"bio": "Xin chào", "display_name": "Alice"}, headers=a["headers"])
    assert r.status_code == 200
    assert r.json()["bio"] == "Xin chào"
    bad = client.put("/api/profile/me", json={"avatar_url": "javascript:alert(1)"}, headers=a["headers"])
    assert bad.status_code == 422
