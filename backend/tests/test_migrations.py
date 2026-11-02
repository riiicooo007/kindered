import pathlib

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent


def test_migration_matches_models(tmp_path):
    """Migration 0001 phải tạo ra đúng schema mà models mô tả (bảng, cột, index, ràng buộc)."""
    import app.models  # noqa: F401
    from app.db.base import Base

    url = f"sqlite:///{tmp_path / 'migration_test.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)

    command.upgrade(cfg, "head")

    engine = create_engine(url)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn, opts={"compare_type": False, "compare_server_default": False})
        diff = compare_metadata(ctx, Base.metadata)
    engine.dispose()
    assert diff == [], f"Models và migration lệch nhau: {diff}"

    command.downgrade(cfg, "base")
