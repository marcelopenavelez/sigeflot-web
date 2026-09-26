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
