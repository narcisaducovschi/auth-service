from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models, schemas, crud, security
from app.dependencies import get_current_user , require_role

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

@app.get("/me", response_model=schemas.UserResponse)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/auth/refresh", response_model=schemas.TokenResponse)
def refresh_token(request: schemas.RefreshRequest, db: Session = Depends(get_db)):
    payload = security.decode_token(request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: se esperaba un refresh token",
        )

    user_id = payload.get("sub")
    user = crud.get_user_by_id(db, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    new_access_token = security.create_access_token(str(user.id))
    new_refresh_token = security.create_refresh_token(str(user.id))

    return schemas.TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )

@app.get("/admin/users", response_model=list[schemas.UserResponse])
def list_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.ADMIN)),
):
    return db.query(models.User).all()