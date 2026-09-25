# Reporte de carga oficial

Resultado local en `sigeflot_migration_test`: carga aplicada dos veces, sin duplicados nuevos.

Conteos validados: 48 vehículos, 34 conductores, 14 proveedores, 18 órdenes, 231 mantenimientos, 14 salidas, 80 componentes y 297 variantes BI. Los datos no presentes en el Excel se conservaron como NULL histórico; no se infirieron DNI, RUC, conductor, destino, motivo ni marca/modelo.

La importación está bloqueada fuera de la base aislada; Railway y producción no se ejecutaron.
