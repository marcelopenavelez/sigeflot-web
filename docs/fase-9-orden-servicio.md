# Fase 9: Crear Orden de Servicio

## Objetivo y referencia

La Fase 9 incorpora la pantalla **Crear Orden de Servicio** para ADMINISTRADOR y MECANICO. La referencia funcional es exactamente `PANTALLAS DE MUESTRA/Captura de pantalla 2026-09-17 034713.jpg`; la interfaz conserva el diseño SIGEFLOT WEB y no replica el Apps Script anterior.

## Arquitectura y datos

La migración `f9a1b2c3d4e5` agregó a `ordenes_servicio` `kilometraje_orden`, `dias_parada`, `estado_archivo` y `descripcion_correctivo`, y permite `monto=NULL` cuando aún no hay costo real. La tabla `orden_servicio_preventivos` relaciona la orden con múltiples elementos de `CatalogoMantenimientoOrigen`; no se almacenan listas CSV ni se usa el catálogo BI como FK.

`estado` describe el ciclo operativo interno de una orden nueva (`ABIERTA`), mientras `estado_archivo` conserva el estado documental (`PENDIENTE` o `ARCHIVADO`). `id` es el identificador SQL interno, `id_orden_origen` conserva trazabilidad histórica y `numero_orden` es el identificador operativo de logística, sin formato forzado.

## Flujo de creación

La ruta `/ordenes/nueva` consume `GET /api/v1/ordenes-servicio/vehicles`, `GET /api/v1/ordenes-servicio/maintenance-catalog`, `GET /api/v1/ordenes-servicio/providers` y `POST /api/v1/ordenes-servicio`. Envía solo número, vehículo, kilometraje, IDs preventivos, correctivo, proveedor opcional y estado de archivo. La fecha visible usa `es-PE` y es informativa: el servidor genera la fecha oficial.

El selector muestra placa y marca/modelo. El kilometraje actual es lectura; cuando es nulo se informa claramente y la nueva lectura se acepta. El backend valida y actualiza la lectura transaccionalmente. El catálogo se consulta con búsqueda, selección múltiple, selección de visibles y limpieza; el correctivo es texto real opcional si existe al menos un preventivo.

## Seguridad, históricos y responsive

ADMINISTRADOR y MECANICO pueden abrir la ruta y usar auxiliares; CHOFER y CONSULTA son redirigidos por el guard frontend y rechazados por el backend. El proveedor es opcional y proviene solo del endpoint de activos.

Los históricos preservan `id_orden_origen`, `numero_orden`, procedencia, relaciones y montos. El importador conserva kilometraje, días de parada, correctivo y estado de archivo para futuras cargas, sin backfill en esta fase.

La pantalla no expone costo, días de parada, estado interno ni campos de procedencia. Es responsive: una columna en teléfono, dos o tres cuando hay espacio, controles táctiles de al menos 44 px, catálogo con scroll vertical y el drawer/hamburguesa existente sin overflow horizontal.
