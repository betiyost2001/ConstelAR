# app/cli/seed_admin.py
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import User
from ..security import hash_password

def seed():
    db: Session = SessionLocal()
    try:
        email = "admin@constelar.app"
        user = db.query(User).filter(User.email == email).first()
        if user:
            print("✔ Admin ya existe:", email)
            return
        u = User(
            name="Admin",
            email=email,
            password_hash=hash_password("Admin123!"),
            role="admin",
            status="active",
        )
        db.add(u)
        db.commit()
        print("✔ Admin creado:", email, "(pass: Admin123!)")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
