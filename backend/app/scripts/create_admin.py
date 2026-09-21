from getpass import getpass
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Role, Usuario

def main() -> None:
    names, last_names, email = input("Nombres: ").strip(), input("Apellidos: ").strip(), input("Email: ").strip()
    password = getpass("Contraseña: ")
    try: validated_email = str(TypeAdapter(EmailStr).validate_python(email))
    except ValidationError: print("Email inválido."); return
    with SessionLocal() as db:
        if db.scalar(select(Usuario).where(Usuario.email == validated_email)):
            print("El email ya está registrado."); return
        role = db.scalar(select(Role).where(Role.codigo == "ADMINISTRADOR"))
        if role is None: print("Rol ADMINISTRADOR no disponible."); return
        try:
            db.add(Usuario(nombres=names, apellidos=last_names, email=validated_email, password_hash=hash_password(password), role_id=role.id)); db.commit()
            print("Administrador creado correctamente.")
        except ValueError as error: db.rollback(); print(str(error))

if __name__ == "__main__": main()
