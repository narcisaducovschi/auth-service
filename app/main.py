from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models, schemas, crud, security

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")


@app.post("/auth/register", response_model=schemas.UserResponse, status_code=201)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user_in.email)
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    return crud.create_user(db, user_in)


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, credentials.email, credentials.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta cuenta está desactivada",
        )

    access_token = security.create_access_token(str(user.id))
    refresh_token = security.create_refresh_token(str(user.id))

    return schemas.TokenResponse(access_token=access_token, refresh_token=refresh_token)