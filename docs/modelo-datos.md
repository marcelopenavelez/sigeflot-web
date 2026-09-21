# Modelo de datos

SIGEFLOT usa MariaDB 10.4.32 y SQLAlchemy 2.x. Las tablas conservan PK, FK, índices de correo/placa y restricciones de unicidad y kilometraje; no se usan borrados en cascada para el historial.

```mermaid
erDiagram
  roles ||--o{ usuarios : asigna
  vehiculos ||--o{ salidas : registra
  conductores ||--o{ salidas : conduce
  vehiculos ||--o{ ordenes_servicio : atiende
  proveedores ||--o{ ordenes_servicio : provee
  vehiculos ||--o{ mantenimientos : recibe
  ordenes_servicio ||--o{ mantenimientos : respalda
```
