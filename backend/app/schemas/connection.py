from pydantic import BaseModel

from app.schemas.common import UTCDatetime
from app.schemas.user import PublicUser


class ConnectionItem(BaseModel):
    connection_id: int
    status: str  # pending | accepted | rejected
    direction: str  # sent | received
    created_at: UTCDatetime
    user: PublicUser


class ConnectionRequestsOut(BaseModel):
    received: list[ConnectionItem]
    sent: list[ConnectionItem]
