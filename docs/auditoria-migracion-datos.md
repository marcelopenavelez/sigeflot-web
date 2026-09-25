# Auditoría de migración de datos oficiales

Fuente auditada: `Control_Flota_DIRESA.xlsx`. El archivo se conserva sin cambios y está ignorado por Git.

| HOJA_ORIGEN | COLUMNA_ORIGEN | TABLA_DESTINO | CAMPO_DESTINO | TIPO_ORIGEN | TIPO_DESTINO | TRANSFORMACION | ESTADO | OBSERVACION |
|---|---|---|---|---|---|---|---|---|
| Flota_Vehicular | Placa | vehiculos | placa | texto | varchar | trim, mayúsculas | DIRECTO | clave natural |
| Flota_Vehicular | Marca_Modelo | vehiculos | marca/modelo | texto | varchar/varchar | no segura | AMBIGUO | no hay separación evidenciada |
| Flota_Vehicular | fechas SOAT/revisión | vehiculos | vencimientos | fecha | date | fecha Excel a date | DIRECTO | |
| Flota_Inactiva | Causal/Fecha_Inactividad_Inicio | vehiculos | estado/observaciones | texto/fecha | varchar/text | no hay campo específico | CAMPO_FALTANTE | preservar historial requiere ampliación |
| Choferes | IDCHOFER | conductores | id_origen | número | inexistente | conservar literal | CAMPO_FALTANTE | documento obligatorio no existe en fuente |
| Choferes | Nombre_Completo | conductores | nombres/apellidos | texto | varchar/varchar | división no segura | AMBIGUO | no inferir apellidos |
| Orden_de_Servicio | ID_Orden | ordenes_servicio | id_orden_origen | texto/mixto | inexistente | conservar literal | CAMPO_FALTANTE | valores numéricos y alfanuméricos |
| HIST MANTENIMIENTO | ID_Registro | mantenimientos | id_origen | número | inexistente | conservar literal | CAMPO_FALTANTE | trazabilidad requerida |
| HIST MANTENIMIENTO | Orden_Servicio | mantenimientos | orden_servicio_origen | mixto | inexistente | sin FK forzada | HISTORICO | coincidencia debe probarse |
| Registro_Salidas | ID_Salida | salidas | id_origen | texto | inexistente | conservar literal | CAMPO_FALTANTE | |
| Registro_Salidas | nombre/placa/km | salidas | conductor/vehículo/km | texto/número | FK/int | placa normalizada | AMBIGUO | faltan conductor, destino y motivo obligatorios |
| Proveedor_Taller | proveedores | razon_social | texto | varchar | trim comparativo | TRANSFORMAR | proveedores no tienen RUC en fuente |

La carga histórica aprobada usa campos nullable únicamente en registros con `es_historico=true`; los CREATE operativos permanecen estrictos. `--apply` solo permite la base exacta `sigeflot_migration_test`.
