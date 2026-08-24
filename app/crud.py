import uuid
from sqlalchemy.orm import Session
from app import models, schemas, security

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
    
    