# Plan de despliegue a producción — Fase 7.4

Este plan no autoriza despliegues ni importaciones. El orden obligatorio es:

1. Backup MySQL Railway.
2. Validar el backup.
3. Merge de código.
4. Railway auto-deploy.
5. Alembic `preDeploy`.
6. Verificar `/health`.
7. Verificar `/health/db`.
8. DRY RUN contra producción.
9. Comparar conteos esperados.
10. Importación oficial.
11. Segunda importación e idempotencia.
12. Validación SQL.
13. Crear usuarios reales.
14. Prueba frontend Netlify.
15. Cierre.

Conteos de aceptación: 48 vehículos, 34 conductores, 14 proveedores, 18 órdenes, 231 mantenimientos, 14 salidas, 80 componentes y 297 variantes BI.

La importación productiva requiere simultáneamente `--apply`, `--production`, `APP_ENV=production`, `SIGEFLOT_ALLOW_PRODUCTION_IMPORT=true` y la confirmación exacta fuera de Git. El respaldo se almacena solo en `database/backups/`, ignorado por Git.
