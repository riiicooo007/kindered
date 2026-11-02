# Kindred — Community Connection Platform
"Find people who understand you."


## Deploy (Render + Neon)

1. Database: Neon
2. Web deploy: render

## Chạy backend trên máy

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
alembic upgrade head               # tạo bảng
python -m scripts.seed             # (tuỳ chọn) 24 user mẫu, mật khẩu Password123!
uvicorn app.main:app --reload
```

- Swagger: http://localhost:8000/docs
- Test: `cd backend && pytest` (dùng DB SQLite riêng, không đụng DB thật)

## Quy ước API

- REST: tiền tố `/api` (vd `POST /api/auth/login`). Frontend gọi `${VITE_API_URL}/api/...`
- Đăng nhập: `POST /api/auth/login` body `{ "identifier": "<username hoặc email>", "password": "..." }`
- Mọi endpoint khác: header `Authorization: Bearer <token>`
- WebSocket (token qua query):
  - `ws://host/ws/chat/{conversation_id}?token=...` — gửi `{"type":"message","content":"..."}`, `{"type":"ping"}`
  - `ws://host/ws/notifications?token=...` — kênh toàn cục: thông báo realtime + `user_status` của bạn bè.
    Frontend nên mở kênh này khi đã đăng nhập (đây là lúc user được tính là online).
  - Sự kiện nhận: `message`, `notification`, `user_status`, `pong`, `error`. Thông báo có thể tới trên cả 2 kênh, hãy khử trùng theo `notification.id`.


