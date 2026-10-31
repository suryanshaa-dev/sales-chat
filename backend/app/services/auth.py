from sqlalchemy import select
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from backend.app.models.user import User

password_hash = PasswordHash.recommended()


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    statement = select(User).where(User.email == email)
    user = db.scalar(statement)

    if user is None:
        return None

    if not password_hash.verify(password, user.hashed_password):
        return None

    return user
