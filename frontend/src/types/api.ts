export type Role = 'ADMINISTRADOR' | 'MECANICO' | 'CHOFER' | 'CONSULTA'
export interface User { id: number; nombres: string; apellidos: string; email: string; rol: Role; activo: boolean }
export interface Vehicle { id: number; placa: string; marca: string; modelo: string; anio: number; tipo: string; kilometraje_actual: number; estado: 'OPERATIVO' | 'MANTENIMIENTO' | 'INACTIVO'; soat_vencimiento: string | null; revision_tecnica_vencimiento: string | null; observaciones: string | null }
export interface VehicleList { items: Vehicle[]; total: number; page: number; page_size: number }
export type VehiclePayload = Omit<Vehicle, 'id'>
/** Exact payload returned by GET /api/v1/salidas/vehicles. */
export interface ExitVehicle {
  id: number
  placa: string
  marca: string | null
  modelo: string | null
  kilometraje_actual: number | null
  estado: string
}
export interface Exit { id: number; vehiculo_id: number; conductor_id: number; fecha_hora_salida: string; kilometraje_salida: number; observaciones: string | null; estado: string }
export interface OrderVehicle { id: number; placa: string; marca: string | null; modelo: string | null; kilometraje_actual: number | null; estado: string }
export interface MaintenanceCatalogItem { id: number; id_componente_origen: string; tarea: string; prioridad: string | null; intervalo_km: number | null; intervalo_dias: number | null }
export interface OrderProvider { id: number; razon_social: string; nombre_comercial: string | null }
export interface OrderCreatePayload { numero_orden: string; vehiculo_id: number; kilometraje_orden: number; preventivo_ids: number[]; descripcion_correctivo?: string | null; proveedor_id?: number | null; estado_archivo: 'PENDIENTE' | 'ARCHIVADO' }
export interface OrderPreventive { id: number; id_componente_origen: string; tarea: string }
export interface OrderResponse { id: number; numero_orden: string; vehiculo_id: number | null; proveedor_id: number | null; fecha: string | null; descripcion: string; descripcion_correctivo: string | null; kilometraje_orden: number | null; dias_parada: number | null; monto: number | null; estado: string; estado_archivo: string | null; es_historico: boolean; fuente_origen: string | null; preventivos: OrderPreventive[] }
export interface OrderListItem { id: number; numero_orden: string; id_orden_origen: string | null; fecha: string | null; placa: string | null; kilometraje_orden: number | null; proveedor: string | null; estado: string; estado_archivo: string | null; es_historico: boolean; monto: number | null; dias_parada: number | null }
export interface OrderListResponse { items: OrderListItem[]; page: number; page_size: number; total: number; pages: number }
export interface OrderFilters { search?: string; placa?: string; estado?: string; estado_archivo?: string; es_historico?: boolean; fecha_desde?: string; fecha_hasta?: string; page?: number; page_size?: number }
export interface OrderPreventiveItem extends OrderPreventive { prioridad: string | null }
export interface OrderDetail extends OrderResponse { id_orden_origen: string | null; placa: string | null; proveedor: string | null; preventivos: OrderPreventiveItem[] }
