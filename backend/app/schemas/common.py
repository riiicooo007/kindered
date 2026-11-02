from datetime import datetime, timezone
from typing import Annotated, Iterable, Optional

from pydantic import AfterValidator


def ensure_utc(value: datetime) -> datetime:
    """SQLite trả datetime naive; luôn chuẩn hóa về UTC có tzinfo."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def clean_list(values: Optional[Iterable[str]], max_items: int = 20, max_len: int = 50) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values or []:
        s = str(v).strip()[:max_len]
        if not s or s.lower() in seen:
            continue
        seen.add(s.lower())
        out.append(s)
        if len(out) >= max_items:
            break
    return out


UTCDatetime = Annotated[datetime, AfterValidator(ensure_utc)]
CleanList = Annotated[list[str], AfterValidator(clean_list)]
