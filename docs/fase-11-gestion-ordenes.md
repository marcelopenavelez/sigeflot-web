# Fase 11: gestión de órdenes

Las órdenes históricas son solo lectura. ADMINISTRADOR y MECANICO pueden editar órdenes operativas ABIERTA, cerrar mediante la transición ABIERTA a CERRADA y cambiar su estado de archivo; CONSULTA solo consulta y CHOFER no accede.

Los endpoints son PATCH de orden, POST de cierre, PATCH de archivo y GET de auditoría. Las mutaciones bloquean la orden, validan proveedor y mantenimiento, conservan NULL y escriben auditoría en la misma transacción. El kilometraje del vehículo solo aumenta.

La migración agrega cierre nullable y auditoría; no crea datos históricos retroactivos. Quedan fuera: reapertura, eliminación, archivos, PDF y facturación.
