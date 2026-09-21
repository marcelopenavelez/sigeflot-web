from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.security import hash_password
from app.models import Role, Usuario
from app.schemas.auth import UserCreate, UserRead

router = APIRouter(prefix="/api/v1/users", tags=["users"])

def admin_required(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol.codigo != "ADMINISTRADOR":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    return user

@router.post("", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _: Usuario = Depends(admin_required)) -> UserRead:
    role = db.scalar(select(Role).where(Role.codigo == payload.role_code))
    if role is None:
        raise HTTPException(status_code=422, detail="Rol inválido")
    user = Usuario(nombres=payload.nombres, apellidos=payload.apellidos, email=str(payload.email), password_hash=hash_password(payload.password), role_id=role.id)
    db.add(user)
    try:
        db.commit(); db.refresh(user)
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail="El correo ya está registrado")
    return UserRead(id=user.id, nombres=user.nombres, apellidos=user.apellidos, email=user.email, rol=role.codigo, activo=user.activo)

@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), _: Usuario = Depends(admin_required)) -> list[UserRead]:
    return [UserRead(id=u.id, nombres=u.nombres, apellidos=u.apellidos, email=u.email, rol=u.rol.codigo, activo=u.activo) for u in db.scalars(select(Usuario)).all()]
