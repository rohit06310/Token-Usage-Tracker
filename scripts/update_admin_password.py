from app.services.db import get_session_factory
from app.models.user import User
from app.core.security import get_password_hash

SessionLocal = get_session_factory()
db = SessionLocal()
try:
    admin = db.query(User).filter(User.email == 'admin@example.com').first()
    if admin:
        admin.hashed_password = get_password_hash('admin123')
        db.commit()
        print("Admin password updated successfully.")
    else:
        print("Admin user not found.")
finally:
    db.close()
