# Fase 8: Registro de salidas responsive

## Objetivo

La Fase 8 incorpora el flujo operativo de **Registro de Salida Vehicular**. El requisito principal es una experiencia **mobile-first para CHOFER**, ya que el registro se realiza principalmente desde un teléfono. La referencia funcional principal es exactamente `PANTALLAS DE MUESTRA/Captura de pantalla 2026-09-17 034646.jpg`.

## Flujo y seguridad

La ruta `/salidas` presenta al usuario autenticado el formulario de Registro de Salida. El frontend usa una protección de ruta: solamente los roles **ADMINISTRADOR**, **MECANICO** y **CHOFER** pueden abrirla; **CONSULTA** es redirigido de forma segura al dashboard aun si escribe la URL manualmente. El enlace de menú también se oculta para CONSULTA, pero no sustituye el guard de ruta.

El servidor mantiene la autoridad: `POST /api/v1/salidas` y `GET /api/v1/salidas/vehicles` exigen JWT y aplican el mismo RBAC. Para registrar, el backend asocia al usuario autenticado con el **Conductor** activo cuyo email coincide, normalizado, con el email del Usuario. No se envía fecha ni hora desde el frontend: `fecha_hora_salida` se genera exclusivamente en el servidor. La fecha/hora visible se muestra en `es-PE`, es informativa y se refresca periódicamente.

`GET /api/v1/salidas/vehicles` abastece el selector con `id`, `placa`, `marca`, `modelo`, `kilometraje_actual` y `estado`. Solo incluye vehículos **OPERATIVO** que no tengan salida ABIERTA. Se preservan los nulos históricos: si `kilometraje_actual` es nulo, la pantalla muestra **“Sin kilometraje registrado”**, no establece `min=0` y bloquea el registro hasta que el vehículo tenga kilometraje.

En `POST /api/v1/salidas`, el kilometraje debe ser entero, no negativo y no menor al kilometraje actual. El servidor vuelve a validar el vehículo OPERATIVO y el kilometraje, previene una salida **ABIERTA** duplicada y bloquea transaccionalmente el vehículo para serializar registros concurrentes. Las salidas operativas nuevas usan `es_historico=false` y `fuente_origen=OPERATIVO`; los datos históricos se preservan y no se reescriben.

## Diseño responsive

En móvil el formulario es de una columna, no genera scroll horizontal y los controles táctiles tienen aproximadamente 44 px o más. Registrar y Cancelar ocupan filas cómodas para el pulgar. La navegación se transforma en menú hamburguesa/drawer, que puede cerrarse con fondo, botón de cierre, enlace de navegación o Escape y limita su ancho para no causar overflow. En tablet y escritorio se habilitan columnas adaptativas y una barra lateral estable, conservando la legibilidad y el flujo operativo.

## Verificación frontend

El proyecto no cuenta con infraestructura de pruebas frontend configurada. No se agregó un framework nuevo para esta fase. La verificación manual requerida consiste en iniciar sesión como CONSULTA, navegar directamente a `/salidas` y confirmar la redirección a `/dashboard`; luego repetir con ADMINISTRADOR, MECANICO y CHOFER, que deben visualizar el formulario. También se comprueban los cierres del drawer y la ausencia de scroll horizontal en una ventana móvil.
