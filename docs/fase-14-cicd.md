# Fase 14: integración continua

La Fase 14 incorpora validación automática para cada pull request dirigido a `main`, cada actualización de `main` y ejecuciones manuales mediante `workflow_dispatch`. El workflow vive en `.github/workflows/ci.yml`, usa permisos de solo lectura sobre el contenido y no contiene pasos de despliegue.

## Checks

- `backend-tests`: usa Python 3.12 y un servicio efímero MySQL 9 con la base exclusiva `sigeflot_ci_test`. Instala las dependencias, espera la base, aplica `alembic upgrade head` y ejecuta la suite completa con `python -m pytest`. El fixture destructivo acepta únicamente `sigeflot_test` y `sigeflot_ci_test`.
- `frontend-quality`: usa Node 24 y caché npm, ejecuta `npm ci`, ESLint y el build Vite con una URL local de API.
- `docker-validation`: genera un `.env.docker` temporal con valores exclusivos de CI, valida Compose y construye las imágenes backend y frontend. No publica imágenes ni levanta el stack completo.
- `api-newman`: se ejecuta después de `backend-tests`, prepara otra base MySQL 9 efímera, aplica Alembic, crea un administrador CI mediante el script oficial `app.scripts.seed_users`, inicia FastAPI y ejecuta la colección `SIGEFLOT-CI.postman_collection.json`.

## API y reporte Newman

La colección CI comprueba `/health`, `/health/db`, login, usuario autenticado, creación/listado de un vehículo ficticio exclusivo de CI y listado paginado de órdenes de servicio. La contraseña y el JWT se generan durante el job, se enmascaran y no se guardan en el repositorio. Newman produce salida CLI y `postman/newman-report.xml` en formato JUnit; GitHub lo conserva como artifact `newman-junit-report` incluso cuando la colección falla.

## Seguridad y despliegue

Las bases, usuarios y credenciales del workflow son efímeros y no pertenecen a desarrollo, QA ni producción. El pipeline no usa Railway, Netlify, S3 ni GitHub Secrets y no ejecuta deploy. Railway conserva el despliegue del backend y sus migraciones de pre-deploy; Netlify conserva el despliegue del frontend.

Para una ejecución local equivalente se requieren MySQL aislado, Python 3.12, Node 24 y Docker. Los reportes Newman y archivos de entorno locales permanecen ignorados por Git.
