"""Create explicitly configured system users without printing credentials."""
import os
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Role, Usuario

ROLES = ("ADMINISTRADOR", "MECANICO", "CHOFER", "CONSULTA")

def main() -> None:
    with SessionLocal() as db:
        for role_code in ROLES:
            prefix = f"SIGEFLOT_{role_code}_"
            values = {key: os.getenv(prefix + key, "").strip() for key in ("NOMBRES", "APELLIDOS", "EMAIL", "PASSWORD")}
            if not any(values.values()):
                continue
            if not all(values.values()):
                print(f"{role_code}: SKIPPED_INCOMPLETE")
                continue
            email = values["EMAIL"].lower()
            if db.scalar(select(Usuario).where(Usuario.email == email)):
                print(f"{role_code}: EXISTS")
                continue
            role = db.scalar(select(Role).where(Role.codigo == role_code))
            if role is None:
                print(f"{role_code}: SKIPPED_ROLE_MISSING")
                continue
            try:
                db.add(Usuario(nombres=values["NOMBRES"], apellidos=values["APELLIDOS"], email=email, password_hash=hash_password(values["PASSWORD"]), role_id=role.id))
                db.commit()
                print(f"{role_code}: CREATED")
            except ValueError:
                db.rollback(); print(f"{role_code}: SKIPPED_PASSWORD_POLICY")

if __name__ == "__main__": main()
