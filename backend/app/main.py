import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import update

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import User
from app.routers import auth, chat, connections, matching, notifications, profile, survey, users, ws

logger = logging.getLogger("kindred")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.SECRET_KEY == "dev-only-secret-change-me":
        logger.warning("Đang dùng SECRET_KEY mặc định - hãy đặt SECRET_KEY riêng khi deploy!")
    # Sau khi server khởi động lại, không còn socket nào => mọi user đều offline
    try:
        with SessionLocal() as db:
            db.execute(update(User).values(is_online=False))
            db.commit()
    except Exception:
        logger.warning("Không reset được trạng thái online (đã chạy 'alembic upgrade head' chưa?)")
    yield


app = FastAPI(title="Kindred API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,  # dùng Bearer token, không dùng cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, users, profile, survey, matching, connections, chat, notifications):
    app.include_router(r.router, prefix="/api")
app.include_router(ws.router)


@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok"}


@app.get("/", tags=["Meta"])
def root():
    return {"name": "Kindred API", "docs": "/docs"}
