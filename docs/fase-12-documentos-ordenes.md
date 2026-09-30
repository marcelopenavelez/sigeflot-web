# Fase 12: documentos y evidencias de órdenes

## Arquitectura de almacenamiento

Los metadatos se almacenan en MariaDB/MySQL mediante `orden_servicio_documentos`. El contenido binario se mantiene fuera de la base mediante la interfaz `StorageBackend`. Desarrollo usa `LocalStorage`; producción debe usar `S3Storage` con un bucket S3-compatible privado. `STORAGE_BACKEND=local` se rechaza si `APP_ENV=production`.

`LocalStorage` escribe bajo `STORAGE_LOCAL_ROOT`, cuya ruta predeterminada es `.data/documentos` desde el directorio de ejecución del backend. Esa ruta está ignorada por Git. `S3Storage` utiliza boto3 y admite endpoint configurable para AWS S3, R2, B2 o MinIO. Las credenciales nunca se devuelven por API ni se guardan en la base.

## Modelo

Cada documento registra orden, nombre original de presentación, nombre UUID almacenado, MIME, extensión, tamaño, categoría, clave privada de storage, fecha, usuario y estado activo. `storage_key` es único; tamaño debe ser positivo; la categoría debe ser `ORDEN_SERVICIO`, `FACTURA`, `INFORME_TECNICO`, `FOTOGRAFIA` u `OTRO`. No existen cascadas destructivas.

## Endpoints y RBAC

- `POST /api/v1/ordenes-servicio/{id}/documentos`: ADMINISTRADOR y MECANICO.
- `GET /api/v1/ordenes-servicio/{id}/documentos`: ADMINISTRADOR, MECANICO y CONSULTA.
- `GET /api/v1/ordenes-servicio/{id}/documentos/{documento_id}`: descarga autenticada para roles de lectura.
- `DELETE /api/v1/ordenes-servicio/{id}/documentos/{documento_id}`: solo ADMINISTRADOR.

CHOFER queda bloqueado. Las órdenes históricas aceptan documentos porque la evidencia no modifica sus campos históricos.

## Seguridad y validación

Se permiten PDF, JPEG y PNG con límite predeterminado de 10 MiB. Se validan conjuntamente extensión final, `Content-Type` y firma binaria. La lectura se realiza por bloques y se detiene al superar el límite. Nombres vacíos, ejecutables, extensiones dobles peligrosas, archivos vacíos y contenido discordante se rechazan.

La clave se genera exclusivamente en servidor como `{STORAGE_PREFIX}/{orden_id}/{uuid}.{extension}`. El nombre proporcionado no participa en la ruta, evitando traversal y sobrescrituras. La descarga valida que el documento esté activo y pertenezca a la orden de la URL, y nunca revela rutas locales o claves privadas.

## Eliminación y auditoría

DELETE realiza baja lógica (`activo=false`) y conserva el objeto físico. Un segundo DELETE devuelve 409. Las acciones `DOCUMENTO_ADJUNTADO` y `DOCUMENTO_ELIMINADO` se registran en `orden_servicio_auditoria` con identificador, nombre, categoría, MIME y tamaño, sin contenido, storage key, credenciales ni JWT.

Metadata y auditoría se confirman en una misma transacción. Si storage falla no se escribe en la base. Si storage funciona pero la transacción falla, se intenta eliminar inmediatamente el objeto como compensación; si esa compensación falla puede quedar un objeto huérfano que deberá tratarse operativamente. No se implementa purga física en esta fase.

## Variables de entorno

`STORAGE_BACKEND`, `STORAGE_LOCAL_ROOT`, `STORAGE_BUCKET`, `STORAGE_ENDPOINT_URL`, `STORAGE_REGION`, `STORAGE_ACCESS_KEY_ID`, `STORAGE_SECRET_ACCESS_KEY`, `STORAGE_PREFIX` y `STORAGE_MAX_FILE_SIZE_BYTES`.

## Limitaciones

No incluye una página documental separada, antivirus, OCR, firma digital, URLs públicas, facturación, notificaciones, generación automática de PDF ni purga de objetos inactivos.

## Interfaz frontend

La sección **Documentos y evidencias** vive dentro del detalle de la orden y funciona para órdenes operativas abiertas, cerradas e históricas. La etiqueta de solo lectura histórica sigue protegiendo los datos de la orden, pero no impide adjuntar evidencia a ADMINISTRADOR o MECANICO.

El listado usa tarjetas responsive sin scroll horizontal global y muestra nombre, categoría, extensión, tamaño legible, fecha/hora `es-PE` y usuario. Si no existen elementos se presenta el estado vacío correspondiente. Los controles mantienen objetivos táctiles de aproximadamente 44 px.

ADMINISTRADOR y MECANICO pueden adjuntar archivos mediante `FormData`; el navegador define automáticamente el boundary multipart. La UI valida archivo, categoría, extensión y límite de 10 MiB antes del envío, muestra estados de subida y refresca listado y auditoría al completar. CONSULTA puede listar y descargar; CHOFER no recibe interfaz documental.

La descarga solicita el contenido como `Blob` mediante el endpoint autenticado, crea una URL temporal, inicia la descarga con el nombre original y revoca la URL. No se construyen URLs públicas de storage.

Solo ADMINISTRADOR ve la acción Eliminar. Antes de la baja lógica se muestra una confirmación que aclara que el documento deja de estar disponible pero se conserva para trazabilidad. La interfaz contempla errores HTTP de autenticación, autorización, inexistencia, conflicto, validación, tamaño y servidor sin mostrar detalles técnicos internos.
