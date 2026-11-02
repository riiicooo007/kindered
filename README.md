# Kindred — Community Connection Platform
"Find people who understand you."


## Deploy (Render + Neon)

1. Neon: tạo project, copy connection string.
2. Render: New → Blueprint → chọn repo (dùng `render.yaml`).
3. Điền biến môi trường: `DATABASE_URL`, `FRONTEND_URL`, `GOOGLE_CLIENT_ID`, `VITE_API_URL`, `VITE_WS_URL`, `VITE_GOOGLE_CLIENT_ID`.
4. Mỗi lần deploy, `alembic upgrade head` tự chạy => dữ liệu giữ nguyên, chỉ cập nhật cấu trúc bảng.
5. Google Cloud Console: thêm domain frontend vào Authorized JavaScript origins.

Khi sửa model: `alembic revision --autogenerate -m "mo ta"` rồi commit file migration.

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


