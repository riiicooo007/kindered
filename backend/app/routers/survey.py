from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Profile, SurveyAnswer, User
from app.schemas.common import clean_list
from app.schemas.survey import SurveyIn, SurveyOut

router = APIRouter(prefix="/survey", tags=["Survey"])


@router.post("", response_model=SurveyOut)
def submit_survey(body: SurveyIn, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    data = body.model_dump()
    if me.survey is None:
        me.survey = SurveyAnswer(**data)
    else:
        for key, value in data.items():
            setattr(me.survey, key, value)

    # Đồng bộ sang profile (chỉ các trường công khai, không đồng bộ story/cảm xúc)
    if me.profile is None:
        me.profile = Profile(display_name=me.username, interests=[])
    me.profile.age_group = body.age_group
    me.profile.situation = body.situation
    me.profile.interests = clean_list(list(body.topics) + list(body.activities))

    db.commit()
    return me.survey


@router.get("/me", response_model=SurveyOut)
def get_my_survey(me: User = Depends(get_current_user)):
    if me.survey is None:
        raise HTTPException(status_code=404, detail="Bạn chưa làm khảo sát")
    return me.survey
