# SIGEFLOT WEB

Sistema Integral de Gestión de Flota y Mantenimiento Vehicular. Proyecto académico del curso **Herramientas y Servicios para Desarrolladores en la Web — ISAM**.

## Objetivo

Definir una base modular y mantenible para una futura plataforma de gestión de flota, sin módulos de negocio, autenticación, bases de datos ni infraestructura de despliegue.

## Tecnologías iniciales

- Frontend: React, TypeScript estricto, Vite, Tailwind CSS y Oxlint.
- Backend: Python, FastAPI, Uvicorn y Pydantic.

## Estructura

```text
sigeflot-web/
├── frontend/        # Aplicación React
├── backend/         # API FastAPI
├── database/        # Reservado para fases posteriores
├── infrastructure/  # Reservado para fases posteriores
├── docs/            # Documentación
├── tests/           # Pruebas futuras
└── .github/         # Automatizaciones futuras
```

## Requisitos

- Node.js 20 o superior
- Python 3.11 o superior

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Disponible en `http://localhost:5173`.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Disponible en `http://127.0.0.1:8000`. Swagger/OpenAPI: `http://127.0.0.1:8000/docs`.

## Estado actual

Fase 1: monorepo, pantalla inicial y endpoints básicos. Base de datos, autenticación, módulos funcionales, Docker, CI/CD y observabilidad quedan pendientes para fases posteriores.
