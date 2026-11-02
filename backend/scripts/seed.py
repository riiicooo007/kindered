"""Tạo ~24 người dùng mẫu để thử Matching/Discover.

Chạy (sau khi `alembic upgrade head`):   python -m scripts.seed
Mật khẩu chung của tài khoản mẫu: Password123!
Chạy lại nhiều lần an toàn: bỏ qua user đã tồn tại.
"""
import random

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Profile, SurveyAnswer, User

PASSWORD = "Password123!"

NAMES = [
    "An", "Bình", "Chi", "Dũng", "Giang", "Hà", "Hùng", "Khánh", "Lan", "Minh", "Nam", "Ngọc",
    "Phúc", "Quân", "Thảo", "Trang", "Tuấn", "Uyên", "Vy", "Yến", "Linh", "Long", "Mai", "Sơn",
]
AGES = ["18-24", "25-34", "35-44", "45+"]
SITUATIONS = ["Sinh viên", "Đi làm văn phòng", "Làm tự do", "Đang tìm việc", "Bố mẹ bỉm sữa", "Khởi nghiệp"]
FEELINGS = ["Căng thẳng", "Cô đơn", "Bình yên", "Hào hứng", "Lạc hướng", "Mệt mỏi"]
GOALS = ["Tìm người tâm sự", "Học hỏi kỹ năng", "Chia sẻ sở thích", "Vượt qua áp lực", "Mở rộng quan hệ"]
TOPICS = ["Công nghệ", "Sách", "Âm nhạc", "Du lịch", "Sức khỏe tinh thần", "Khởi nghiệp", "Phim ảnh", "Nấu ăn"]
ACTIVITIES = ["Đọc sách", "Chạy bộ", "Chơi game", "Nghe nhạc", "Đi cà phê", "Viết lách", "Xem phim", "Leo núi"]
STYLES = ["Nhẹ nhàng, chậm rãi", "Sôi nổi, hài hước", "Sâu sắc, nghiêm túc"]
STORIES = [
    "Dạo này công việc áp lực nhiều, mình muốn tìm người cùng chia sẻ và lắng nghe nhau.",
    "Mình mới chuyển đến thành phố mới nên chưa quen nhiều người, rất mong có bạn đồng điệu.",
    "Mình thích đọc sách và viết lách, hay thức khuya suy nghĩ về cuộc sống.",
    "Đang học cách cân bằng giữa học tập, công việc và thời gian cho bản thân.",
    "Mình yêu công nghệ và âm nhạc, muốn tìm bạn cùng trò chuyện về những điều mình thích.",
    "Sau một giai đoạn khó khăn, mình đang học cách chăm sóc sức khỏe tinh thần tốt hơn.",
]


def main() -> None:
    rng = random.Random(42)
    created = 0
    with SessionLocal() as db:
        for i, name in enumerate(NAMES, start=1):
            username = f"seed_user_{i:02d}"
            if db.scalar(select(User.id).where(User.username == username)):
                continue

            age = rng.choice(AGES)
            situation = rng.choice(SITUATIONS)
            topics = rng.sample(TOPICS, k=rng.randint(2, 4))
            activities = rng.sample(ACTIVITIES, k=rng.randint(2, 3))

            user = User(email=f"{username}@example.com", username=username, hashed_password=hash_password(PASSWORD))
            user.profile = Profile(
                display_name=name,
                bio=f"Xin chào, mình là {name}. Rất vui được làm quen!",
                age_group=age,
                situation=situation,
                interests=topics + activities,
            )
            user.survey = SurveyAnswer(
                age_group=age,
                situation=situation,
                recent_feeling=rng.choice(FEELINGS),
                goals=rng.sample(GOALS, k=rng.randint(1, 3)),
                topics=topics,
                activities=activities,
                chat_style=rng.choice(STYLES),
                story=rng.choice(STORIES),
            )
            db.add(user)
            created += 1
        db.commit()
    print(f"Đã tạo {created} người dùng mẫu. Đăng nhập: seed_user_01 / {PASSWORD}")


if __name__ == "__main__":
    main()
