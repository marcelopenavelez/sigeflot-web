# Fase 10: historial y consulta de órdenes

## Objetivo

Consulta de órdenes históricas y operativas sin edición, eliminación ni cambios administrativos.

## API y permisos

`GET /api/v1/ordenes-servicio` admite búsqueda, placa, estado, estado de archivo, tipo histórico, fechas y paginación (máximo 100). ADMINISTRADOR, MECANICO y CONSULTA pueden leer; CHOFER no. `GET /api/v1/ordenes-servicio/{id}` entrega el detalle y preventivos relacionados. POST mantiene la restricción de Fase 9.

## Frontend y QA

Las rutas `/ordenes` y `/ordenes/:id` presentan filtros, paginación, tabla en escritorio y tarjetas en móvil. Se validó contra `sigeflot_local_qa`, sin modificar órdenes históricas ni inventar valores NULL.

## Decisiones y límite de Fase 11

Los filtros se aplican en SQL con joins y conteo paginado; el detalle usa `selectinload` para evitar N+1. No se creó migración: las relaciones y campos ya existían. Fase 11 podrá abordar edición, cierre, archivos, PDF o facturación con reglas explícitas.
