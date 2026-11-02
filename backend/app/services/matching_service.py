"""Matching engine: TF-IDF + Cosine Similarity + điểm cộng theo quy tắc.

Phần thuật toán (UserFeatures -> compute_matches) KHÔNG phụ thuộc DB nên test độc lập được.
Thang điểm (tối đa 100):
    cosine  : 0..72  (cosine >= COSINE_SATURATION được tính đủ 72)
    cùng độ tuổi            : +8
    cùng hoàn cảnh          : +8
    mỗi sở thích chung      : +4 (tối đa +12)
"""
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

if TYPE_CHECKING:  # import muộn trong get_suggestions để phần thuật toán test được riêng
    from sqlalchemy.orm import Session

    from app.models import User

COSINE_SATURATION = 0.6
COSINE_MAX_POINTS = 72.0
BONUS_SAME_AGE = 8.0
BONUS_SAME_SITUATION = 8.0
BONUS_PER_COMMON_INTEREST = 4.0
BONUS_COMMON_INTEREST_CAP = 12.0

_STOPWORDS = {
    "và", "là", "của", "có", "không", "một", "những", "các", "cho", "với", "được", "trong",
    "này", "đó", "tôi", "mình", "em", "anh", "chị", "bạn", "rất", "cũng", "như", "khi", "để",
    "thì", "mà", "nhưng", "nên", "đang", "đã", "sẽ", "ở", "từ", "về", "hay", "hoặc",
}


@dataclass
class UserFeatures:
    user_id: int
    age_group: Optional[str] = None
    situation: Optional[str] = None
    recent_feeling: Optional[str] = None
    goals: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    activities: list[str] = field(default_factory=list)
    chat_style: Optional[str] = None
    story: Optional[str] = None
    bio: Optional[str] = None


@dataclass
class MatchCandidate:
    user_id: int
    score: float
    cosine: float
    common_interests: list[str]
    reasons: list[str]


def _norm(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _slug(value: Optional[str]) -> str:
    return re.sub(r"\W+", "_", _norm(value)).strip("_")


def _free_text_tokens(text: Optional[str]) -> list[str]:
    words = re.findall(r"\w+", _norm(text))
    return [f"từ_{w}" for w in words if len(w) > 1 and w not in _STOPWORDS]


def build_text(f: UserFeatures) -> str:
    """Ghép các trường thành chuỗi có tiền tố ngữ nghĩa, ví dụ: hoàn_cảnh_đi_làm chủ_đề_công_nghệ."""
    parts: list[str] = []

    def add(prefix: str, value: Optional[str]) -> None:
        s = _slug(value)
        if s:
            parts.append(f"{prefix}_{s}")

    add("độ_tuổi", f.age_group)
    add("hoàn_cảnh", f.situation)
    add("cảm_xúc", f.recent_feeling)
    add("phong_cách", f.chat_style)
    for g in f.goals:
        add("mục_tiêu", g)
    for t in f.topics:
        add("chủ_đề", t)
    for a in f.activities:
        add("hoạt_động", a)
    parts += _free_text_tokens(f.story)
    parts += _free_text_tokens(f.bio)
    return " ".join(parts)


# Cache bản vector hóa gần nhất: chỉ fit lại khi dữ liệu thay đổi
_CACHE: Optional[tuple] = None


def _vectorize(ids: tuple, texts: tuple):
    global _CACHE
    cached = _CACHE
    if cached is not None and cached[0] == (ids, texts):
        return cached[1]
    matrix = TfidfVectorizer(token_pattern=r"\S+", lowercase=False, sublinear_tf=True).fit_transform(texts)
    _CACHE = ((ids, texts), matrix)
    return matrix


def _interest_map(f: UserFeatures) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in list(f.topics) + list(f.activities):
        key = _norm(item)
        if key and key not in result:
            result[key] = item.strip()
    return result


def _shared(a: Sequence[str], b: Sequence[str]) -> list[str]:
    b_keys = {_norm(x) for x in b}
    return [x.strip() for x in a if _norm(x) in b_keys]


def compute_matches(all_features: Sequence[UserFeatures], me_id: int) -> list[MatchCandidate]:
    ids = [f.user_id for f in all_features]
    if me_id not in ids or len(ids) < 2:
        return []

    texts = [build_text(f) for f in all_features]
    try:
        matrix = _vectorize(tuple(ids), tuple(texts))
    except ValueError:  # toàn bộ văn bản rỗng -> không có từ vựng
        return []

    me_idx = ids.index(me_id)
    me = all_features[me_idx]
    sims = cosine_similarity(matrix[me_idx], matrix).ravel()
    my_interests = _interest_map(me)

    results: list[MatchCandidate] = []
    for i, other in enumerate(all_features):
        if other.user_id == me_id:
            continue

        cos = float(sims[i])
        common = [display for key, display in my_interests.items() if key in _interest_map(other)]
        same_age = bool(_norm(me.age_group)) and _norm(me.age_group) == _norm(other.age_group)
        same_sit = bool(_norm(me.situation)) and _norm(me.situation) == _norm(other.situation)

        score = COSINE_MAX_POINTS * min(1.0, cos / COSINE_SATURATION)
        score += BONUS_SAME_AGE if same_age else 0.0
        score += BONUS_SAME_SITUATION if same_sit else 0.0
        score += min(BONUS_COMMON_INTEREST_CAP, BONUS_PER_COMMON_INTEREST * len(common))

        reasons: list[str] = []
        if same_age:
            reasons.append(f"Cùng nhóm tuổi {me.age_group}")
        if same_sit:
            reasons.append(f"Cùng hoàn cảnh: {me.situation}")
        if common:
            reasons.append("Cùng quan tâm: " + ", ".join(common[:3]))
        shared_goals = _shared(me.goals, other.goals)
        if shared_goals:
            reasons.append("Cùng mục tiêu: " + ", ".join(shared_goals[:2]))
        if _norm(me.chat_style) and _norm(me.chat_style) == _norm(other.chat_style):
            reasons.append(f"Cùng phong cách trò chuyện: {me.chat_style}")
        if not reasons:
            reasons.append(
                "Cách chia sẻ của hai bạn khá tương đồng" if cos >= 0.1 else "Có thể mang đến góc nhìn mới cho bạn"
            )

        results.append(
            MatchCandidate(
                user_id=other.user_id,
                score=round(min(100.0, max(0.0, score)), 1),
                cosine=round(cos, 4),
                common_interests=common,
                reasons=reasons[:4],
            )
        )

    results.sort(key=lambda r: (-r.score, r.user_id))
    return results


def features_from_user(user: "User") -> UserFeatures:
    s = user.survey
    return UserFeatures(
        user_id=user.id,
        age_group=s.age_group if s else None,
        situation=s.situation if s else None,
        recent_feeling=s.recent_feeling if s else None,
        goals=list(s.goals or []) if s else [],
        topics=list(s.topics or []) if s else [],
        activities=list(s.activities or []) if s else [],
        chat_style=s.chat_style if s else None,
        story=s.story if s else None,
        bio=user.profile.bio if user.profile else None,
    )


def get_suggestions(
    db: "Session",
    me: "User",
    age_group: Optional[str] = None,
    situation: Optional[str] = None,
    interest: Optional[str] = None,
    limit: int = 20,
) -> list[tuple["User", MatchCandidate]]:
    from sqlalchemy import select

    from app.models import SurveyAnswer, User

    users = list(db.scalars(select(User).join(SurveyAnswer, SurveyAnswer.user_id == User.id)))
    candidates = compute_matches([features_from_user(u) for u in users], me.id)
    by_id = {u.id: u for u in users}

    age_q, sit_q, int_q = _norm(age_group), _norm(situation), _norm(interest)
    out: list[tuple["User", MatchCandidate]] = []
    for c in candidates:
        u = by_id[c.user_id]
        s = u.survey
        if age_q and _norm(s.age_group) != age_q:
            continue
        if sit_q and _norm(s.situation) != sit_q:
            continue
        if int_q and not any(int_q in _norm(x) for x in list(s.topics or []) + list(s.activities or [])):
            continue
        out.append((u, c))
        if len(out) >= limit:
            break
    return out
