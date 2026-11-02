import pytest
from starlette.websockets import WebSocketDisconnect


def test_cannot_connect_to_self_or_unknown(client, register):
    a = register("alice")
    assert client.post(f"/api/connections/request/{a['id']}", headers=a["headers"]).status_code == 400
    assert client.post("/api/connections/request/9999", headers=a["headers"]).status_code == 404


def test_duplicate_and_reverse_requests_blocked(client, register):
    a, b = register("alice"), register("bob")
    assert client.post(f"/api/connections/request/{b['id']}", headers=a["headers"]).status_code == 201
    assert client.post(f"/api/connections/request/{b['id']}", headers=a["headers"]).status_code == 400
    assert client.post(f"/api/connections/request/{a['id']}", headers=b["headers"]).status_code == 400


def test_only_receiver_can_accept_or_reject(client, register):
    a, b, c = register("alice"), register("bob"), register("carol")
    cid = client.post(f"/api/connections/request/{b['id']}", headers=a["headers"]).json()["connection_id"]
    assert client.put(f"/api/connections/{cid}/accept", headers=a["headers"]).status_code == 403
    assert client.put(f"/api/connections/{cid}/accept", headers=c["headers"]).status_code == 403
    assert client.put(f"/api/connections/{cid}/accept", headers=b["headers"]).status_code == 200
    assert client.put(f"/api/connections/{cid}/reject", headers=b["headers"]).status_code == 400  # đã xử lý


def test_lists_and_reject_then_resend(client, register):
    a, b = register("alice"), register("bob")
    cid = client.post(f"/api/connections/request/{b['id']}", headers=a["headers"]).json()["connection_id"]

    reqs_b = client.get("/api/connections/requests", headers=b["headers"]).json()
    assert len(reqs_b["received"]) == 1 and reqs_b["sent"] == []
    assert len(client.get("/api/connections/requests", headers=a["headers"]).json()["sent"]) == 1

    assert client.put(f"/api/connections/{cid}/reject", headers=b["headers"]).status_code == 200
    assert client.get("/api/connections/requests", headers=b["headers"]).json()["received"] == []
    assert client.get("/api/connections/friends", headers=a["headers"]).json() == []

    # bị từ chối vẫn được gửi lại
    assert client.post(f"/api/connections/request/{b['id']}", headers=a["headers"]).status_code == 201


def test_friends_list_and_notifications(client, register, befriend):
    a, b = register("alice"), register("bob")
    befriend(a, b)
    assert [f["user"]["id"] for f in client.get("/api/connections/friends", headers=a["headers"]).json()] == [b["id"]]
    assert [f["user"]["id"] for f in client.get("/api/connections/friends", headers=b["headers"]).json()] == [a["id"]]

    # bob nhận thông báo lời mời; alice nhận thông báo đã chấp nhận
    nb = client.get("/api/notifications", headers=b["headers"]).json()
    assert nb["unread_count"] == 1 and nb["items"][0]["type"] == "connection_request"
    na = client.get("/api/notifications", headers=a["headers"]).json()
    assert na["items"][0]["type"] == "connection_accepted"

    nid = nb["items"][0]["id"]
    assert client.put(f"/api/notifications/{nid}/read", headers=b["headers"]).json()["is_read"] is True
    assert client.get("/api/notifications", headers=b["headers"]).json()["unread_count"] == 0
    # không đọc được thông báo của người khác
    assert client.put(f"/api/notifications/{na['items'][0]['id']}/read", headers=b["headers"]).status_code == 404

    assert client.put("/api/notifications/read-all", headers=a["headers"]).json()["unread_count"] == 0
    assert client.get("/api/notifications", headers=a["headers"]).json()["unread_count"] == 0


def test_chat_requires_friendship(client, register, befriend):
    a, b, c = register("alice"), register("bob"), register("carol")
    assert client.post("/api/chat/conversations", json={"user_id": b["id"]}, headers=a["headers"]).status_code == 403
    befriend(a, b)
    r1 = client.post("/api/chat/conversations", json={"user_id": b["id"]}, headers=a["headers"])
    r2 = client.post("/api/chat/conversations", json={"user_id": a["id"]}, headers=b["headers"])
    assert r1.status_code == 200 and r1.json()["id"] == r2.json()["id"]  # cùng 1 phòng
    cid = r1.json()["id"]
    # người ngoài không đọc/gửi được
    assert client.get(f"/api/chat/conversations/{cid}/messages", headers=c["headers"]).status_code == 403
    assert client.post(f"/api/chat/conversations/{cid}/messages", json={"content": "hi"}, headers=c["headers"]).status_code == 403


def test_rest_messages_history_and_message_notification(client, register, befriend):
    a, b = register("alice"), register("bob")
    befriend(a, b)
    cid = client.post("/api/chat/conversations", json={"user_id": b["id"]}, headers=a["headers"]).json()["id"]

    for text in ("một", "hai"):
        r = client.post(f"/api/chat/conversations/{cid}/messages", json={"content": text}, headers=a["headers"])
        assert r.status_code == 201 and r.json()["sender_id"] == a["id"]
    assert client.post(f"/api/chat/conversations/{cid}/messages", json={"content": "   "}, headers=a["headers"]).status_code == 422

    history = client.get(f"/api/chat/conversations/{cid}/messages", headers=b["headers"]).json()
    assert [m["content"] for m in history] == ["một", "hai"]  # cũ -> mới

    convs = client.get("/api/chat/conversations", headers=b["headers"]).json()
    assert convs[0]["last_message"]["content"] == "hai"
    assert convs[0]["other_user"]["id"] == a["id"]

    # bob có đúng 1 thông báo tin nhắn chưa đọc (không spam)
    items = client.get("/api/notifications", headers=b["headers"]).json()["items"]
    assert [n["type"] for n in items].count("new_message") == 1


def test_websocket_chat_roundtrip(client, register, befriend):
    a, b = register("alice"), register("bob")
    befriend(a, b)
    cid = client.post("/api/chat/conversations", json={"user_id": b["id"]}, headers=a["headers"]).json()["id"]

    with client.websocket_connect(f"/ws/chat/{cid}?token={a['token']}") as ws:
        ws.send_json({"type": "ping"})
        assert ws.receive_json() == {"type": "pong"}
        ws.send_json({"type": "message", "content": "Chào Bob"})
        event = ws.receive_json()
        assert event["type"] == "message"
        assert event["message"]["content"] == "Chào Bob"
        assert event["message"]["sender_id"] == a["id"]

    history = client.get(f"/api/chat/conversations/{cid}/messages", headers=b["headers"]).json()
    assert [m["content"] for m in history] == ["Chào Bob"]


def test_websocket_rejects_bad_token_and_non_members(client, register, befriend):
    a, b, c = register("alice"), register("bob"), register("carol")
    befriend(a, b)
    cid = client.post("/api/chat/conversations", json={"user_id": b["id"]}, headers=a["headers"]).json()["id"]

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/chat/{cid}?token=garbage"):
            pass
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/chat/{cid}?token={c['token']}"):
            pass
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/notifications"):
            pass


def test_online_status_updates_via_websocket(client, register, befriend):
    a, b = register("alice"), register("bob")
    befriend(a, b)
    assert client.get(f"/api/users/{a['id']}", headers=b["headers"]).json()["is_online"] is False

    with client.websocket_connect(f"/ws/notifications?token={a['token']}") as ws:
        ws.send_json({"type": "ping"})
        assert ws.receive_json() == {"type": "pong"}  # chắc chắn đã register + announce xong
        assert client.get(f"/api/users/{a['id']}", headers=b["headers"]).json()["is_online"] is True

    after = client.get(f"/api/users/{a['id']}", headers=b["headers"]).json()
    assert after["is_online"] is False
    assert after["last_seen"] is not None
