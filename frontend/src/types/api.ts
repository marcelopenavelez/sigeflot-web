export type Role = 'ADMINISTRADOR' | 'MECANICO' | 'CHOFER' | 'CONSULTA'
export interface User { id: number; nombres: string; apellidos: string; email: string; rol: Role; activo: boolean }
export interface Vehicle { id: number; placa: string; marca: string; modelo: string; anio: number; tipo: string; kilometraje_actual: number; estado: 'OPERATIVO' | 'MANTENIMIENTO' | 'INACTIVO'; soat_vencimiento: string | null; revision_tecnica_vencimiento: string | null; observaciones: string | null }
export interface VehicleList { items: Vehicle[]; total: number; page: number; page_size: number }
export type VehiclePayload = Omit<Vehicle, 'id'>
