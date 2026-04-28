from app.db.database import SessionLocal
from app.models.sqlmodels import User, UserRole
from app.core.security import get_password_hash

db = SessionLocal()

admin = User(
    name="Admin",
    email="admin@test.com",
    password_hash=get_password_hash("admin"),
    role=UserRole.ADMIN
)

db.add(admin)
db.commit()
db.close()