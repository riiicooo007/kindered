from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.matching import MatchResult
from app.schemas.user import PublicUser
from app.services.connection_service import status_map
from app.services.matching_service import get_suggestions

router = APIRouter(prefix="/matching", tags=["Matching"])


@router.get("/suggestions", response_model=list[MatchResult])
def suggestions(
    age_group: Optional[str] = Query(default=None, max_length=50),
    situation: Optional[str] = Query(default=None, max_length=100),
    interest: Optional[str] = Query(default=None, max_length=50),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if me.survey is None:
        raise HTTPException(status_code=400, detail="Bạn cần hoàn thành khảo sát trước khi xem gợi ý")

    pairs = get_suggestions(db, me, age_group=age_group, situation=situation, interest=interest, limit=limit)
    smap = status_map(db, me.id, [u.id for u, _ in pairs])
    results = []
    for user, cand in pairs:
        label, conn_id = smap.get(user.id, (None, None))
        results.append(
            MatchResult(
                user=PublicUser.from_user(user, label, conn_id),
                score=cand.score,
                common_interests=cand.common_interests,
                reasons=cand.reasons,
            )
        )
    return results
