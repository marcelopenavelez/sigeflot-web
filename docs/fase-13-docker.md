# Fase 13: entorno local con Docker Compose

## Requisitos

- Docker Desktop con backend WSL 2.
- Docker Compose v2 o posterior.
- Una copia local ignorada de `.env.docker`, creada a partir de `.env.docker.example` y con secretos exclusivos de desarrollo.

El entorno es paralelo a producción: utiliza MySQL y almacenamiento documental locales. No usa Railway, Netlify ni S3.

## Servicios

- `db`: MySQL 9 accesible únicamente dentro de `sigeflot-network`.
- `migrate`: aplica `alembic upgrade head` después de que MySQL esté saludable y termina con código cero.
- `backend`: FastAPI en `http://localhost:8000`, ejecutado por un usuario no-root.
- `frontend`: Vite en `http://localhost:5173`, ejecutado por el usuario no-root de la imagen Node.

Los volúmenes `sigeflot_mysql_data` y `sigeflot_documents` preservan respectivamente la base de datos y los documentos locales.

## Uso

Validar la configuración:

```powershell
docker compose --env-file .env.docker config
```

Construir y arrancar:

```powershell
docker compose --env-file .env.docker up -d --build
```

Consultar estado y logs:

```powershell
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs
```

Detener sin eliminar datos:

```powershell
docker compose --env-file .env.docker down
```

`docker compose down -v` elimina de forma destructiva los volúmenes y solo debe utilizarse para un reinicio completo e intencional del entorno local.
