# Módulo de vehículos

Gestiona `vehiculos` mediante `/api/v1/vehicles`. Administradores crean e inactivan; administradores y mecánicos actualizan; cualquier rol autenticado consulta. La placa se normaliza a mayúsculas y el kilometraje nunca puede disminuir. `DELETE` realiza baja lógica: cambia el estado a `INACTIVO`, sin borrar historial.

El listado usa `page`, `page_size` (máximo 100), `search`, `estado` y `tipo`.
