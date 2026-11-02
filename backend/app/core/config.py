from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./community.db"
    SECRET_KEY: str = "dev-only-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    GOOGLE_CLIENT_ID: str = ""
    # Nhiều domain thì ngăn cách bằng dấu phẩy
    FRONTEND_URL: str = "http://localhost:5173"

    @property
    def sqlalchemy_url(self) -> str:
        url = self.DATABASE_URL.strip()
        if url.startswith("postgres://"):  # một số nhà cung cấp dùng scheme cũ
            url = "postgresql://" + url[len("postgres://"):]
        return url

    @property
    def is_sqlite(self) -> bool:
        return self.sqlalchemy_url.startswith("sqlite")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.FRONTEND_URL.split(",") if o.strip()]


settings = Settings()
