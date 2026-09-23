# Preparación de despliegue

Esta fase prepara el repositorio; no publica la aplicación.

## Backend en Railway

Railway usa `railway.toml`: instala `backend/requirements.txt` y ejecuta Uvicorn desde `backend` en `0.0.0.0:$PORT`. `uvicorn[standard]` ya es una dependencia del backend. Conecte el repositorio de GitHub en Railway y configure estas variables en el panel del servicio, nunca en Git:

- `DATABASE_URL`: URL SQLAlchemy compatible con MySQL/MariaDB, por ejemplo con el prefijo `mysql+pymysql://`.
- `JWT_SECRET_KEY`: secreto aleatorio largo para firmar los JWT.
- `CORS_ORIGINS`: lista separada por comas. Conserve los orígenes locales y agregue el dominio HTTPS de Netlify cuando exista.
- Opcionalmente `APP_ENV=production` y `ACCESS_TOKEN_EXPIRE_MINUTES`.

Para usar MySQL en Railway, cree o conecte un servicio MySQL, obtenga sus datos de conexión desde el panel y forme `DATABASE_URL` como variable privada. No use la base de desarrollo local ni publique sus credenciales. Tras desplegar, Railway genera un dominio público del backend; úselo como valor de `VITE_API_URL` en Netlify.

## Frontend en Netlify

`netlify.toml` define `frontend` como base, `npm run build` como compilación y `dist` como publicación. `frontend/public/_redirects` mantiene las rutas de React Router al recargar una página.

En el sitio de Netlify configure `VITE_API_URL` con el dominio público HTTPS de Railway, sin barra final. Vite incorpora esa variable durante el build, por lo que cualquier cambio requiere una nueva compilación. No coloque JWT, contraseñas, secretos ni `DATABASE_URL` en variables públicas de Netlify.
