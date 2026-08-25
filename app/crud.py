import uuid
import secrets
from sqlalchemy.orm import Session
from app import models, schemas, security
from datetime import datetime, timedelta, timezone

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: uuid.UUID) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session , user_in: schemas.UserCreate) -> models.User:
    hashed_password = security.hash_password(user_in.password)
    db_user = models.User(
        email = user_in.email,
        hashed_password = hashed_password,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user

def create_password_reset_token(db: Session , user_id: uuid.UUID) -> models.PasswordResetToken:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    reset_token = models.PasswordResetToken(
        user_id = user_id,
        token = token,
        expires_at = expires_at,
    )

    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token

def get_valid_reset_token(db: Session, token: str) -> models.PasswordResetToken | None:
    reset_token = (
        db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.token == token)
        .first()
    )

    if reset_token is None:
        return None
    if reset_token.used:
        return None
    if reset_token.expires_at < datetime.now(timezone.utc):
        return None

    return reset_token


def reset_user_password(db: Session, reset_token: models.PasswordResetToken, new_password: str) -> None:
    user = get_user_by_id(db, reset_token.user_id)
    user.hashed_password = security.hash_password(new_password)

    reset_token.used = True

    db.commit()
    