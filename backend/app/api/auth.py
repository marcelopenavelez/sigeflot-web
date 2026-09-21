import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, UserRead

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
bearer = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> Usuario:
    from app.core.security import decode_access_token
    try:
        claims = decode_access_token(credentials.credentials)
        user = db.scalar(select(Usuario).where(Usuario.id == int(str(claims["sub"]))))
    except (jwt.PyJWTError, KeyError, ValueError):
        user = None
    if user is None or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado", headers={"WWW-Authenticate": "Bearer"})
    return user

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(Usuario).where(Usuario.email == str(payload.email)))
    if user is None or not user.activo or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return TokenResponse(access_token=create_access_token(str(user.id), user.rol.codigo), expires_in=1800)

@router.get("/me", response_model=UserRead)
def me(user: Usuario = Depends(get_current_user)) -> UserRead:
    return UserRead(id=user.id, nombres=user.nombres, apellidos=user.apellidos, email=user.email, rol=user.rol.codigo, activo=user.activo)
