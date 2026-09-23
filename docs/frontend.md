# Frontend SIGEFLOT WEB

La SPA React usa Vite, TypeScript, Tailwind CSS y `react-router-dom`. El cliente API centralizado está en `frontend/src/services/api.ts`; toma la URL desde `VITE_API_URL` (por defecto, `http://127.0.0.1:8000`).

Rutas: `/login`, `/dashboard` y `/vehicles`. Las dos últimas están protegidas: el token JWT se guarda en `localStorage` y se envía como `Authorization: Bearer` en las solicitudes al backend. El contexto consulta `/api/v1/auth/me` al restaurar la sesión y permite cerrarla.

Roles visibles: ADMINISTRADOR puede crear, editar e inactivar; MECANICO puede editar; CHOFER y CONSULTA solo pueden consultar. El backend mantiene la autoridad y valida cada permiso.

Para iniciar: copie `.env.example` a `.env` solo si necesita otra URL de API, ejecute `npm run dev` desde `frontend` y mantenga FastAPI en `127.0.0.1:8000`. La aplicación incluye `public/_redirects` para el enrutamiento de SPA en una futura publicación en Netlify; no se ha realizado ningún despliegue.
