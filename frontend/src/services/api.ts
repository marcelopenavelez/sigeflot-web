import type { Exit, ExitVehicle, MaintenanceCatalogItem, OrderArchiveUpdate, OrderAuditResponse, OrderCloseResponse, OrderCreatePayload, OrderDetail, OrderDocumentCategory, OrderDocumentItem, OrderFilters, OrderListResponse, OrderProvider, OrderResponse, OrderUpdatePayload, OrderVehicle, User, Vehicle, VehicleList, VehiclePayload } from '../types/api'

const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const TOKEN_KEY = 'sigeflot_access_token'
export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (token: string) => localStorage.setItem(TOKEN_KEY, token)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const token = getToken(); if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (response.status === 204) return undefined as T
  const body = await response.json().catch(() => ({})) as { detail?: unknown }
  if (!response.ok) throw new ApiError(response.status, typeof body.detail === 'string' ? body.detail : 'No fue posible completar la operación.')
  return body as T
}
async function requestBlob(path: string): Promise<Blob> {
  const headers = new Headers({ Accept: 'application/pdf,image/jpeg,image/png' })
  const token = getToken(); if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: unknown }
    throw new ApiError(response.status, typeof body.detail === 'string' ? body.detail : 'No fue posible descargar el documento.')
  }
  return response.blob()
}
export const api = {
  login: (email: string, password: string) => request<{ access_token: string }>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request<User>('/api/v1/auth/me'),
  vehicles: (params = new URLSearchParams()) => request<VehicleList>(`/api/v1/vehicles?${params}`),
  createVehicle: (payload: Partial<VehiclePayload>) => request<Vehicle>('/api/v1/vehicles', { method: 'POST', body: JSON.stringify(payload) }),
  updateVehicle: (id: number, payload: Partial<VehiclePayload>) => request<Vehicle>(`/api/v1/vehicles/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deactivateVehicle: (id: number) => request<void>(`/api/v1/vehicles/${id}`, { method: 'DELETE' }),
  availableExitVehicles: () => request<ExitVehicle[]>('/api/v1/salidas/vehicles'),
  createExit: (payload: { vehiculo_id: number; kilometraje_salida: number; observaciones?: string }) => request<Exit>('/api/v1/salidas', { method: 'POST', body: JSON.stringify(payload) }),
  orderVehicles: () => request<OrderVehicle[]>('/api/v1/ordenes-servicio/vehicles'),
  maintenanceCatalog: (search = '') => request<MaintenanceCatalogItem[]>(`/api/v1/ordenes-servicio/maintenance-catalog?${new URLSearchParams(search ? { search } : '')}`),
  orderProviders: () => request<OrderProvider[]>('/api/v1/ordenes-servicio/providers'),
  createOrder: (payload: OrderCreatePayload) => request<OrderResponse>('/api/v1/ordenes-servicio', { method: 'POST', body: JSON.stringify(payload) }),
  orders: (params: OrderFilters = {}) => request<OrderListResponse>(`/api/v1/ordenes-servicio?${new URLSearchParams(Object.entries(params).filter(([, value]) => value !== undefined && value !== '').map(([key, value]) => [key, String(value)]))}`),
  getOrder: (id: number) => request<OrderDetail>(`/api/v1/ordenes-servicio/${id}`),
  updateOrder: (id: number, payload: OrderUpdatePayload) => request<OrderResponse>(`/api/v1/ordenes-servicio/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  closeOrder: (id: number) => request<OrderCloseResponse>(`/api/v1/ordenes-servicio/${id}/cerrar`, { method: 'POST' }),
  updateOrderArchive: (id: number, payload: OrderArchiveUpdate) => request<OrderResponse>(`/api/v1/ordenes-servicio/${id}/archivo`, { method: 'PATCH', body: JSON.stringify(payload) }),
  getOrderAudit: (id: number) => request<OrderAuditResponse>(`/api/v1/ordenes-servicio/${id}/auditoria`),
  listOrderDocuments: (orderId: number) => request<OrderDocumentItem[]>(`/api/v1/ordenes-servicio/${orderId}/documentos`),
  uploadOrderDocument: (orderId: number, file: File, categoria: OrderDocumentCategory) => {
    const body = new FormData(); body.append('file', file); body.append('categoria', categoria)
    return request<OrderDocumentItem>(`/api/v1/ordenes-servicio/${orderId}/documentos`, { method: 'POST', body })
  },
  downloadOrderDocument: (orderId: number, documentId: number) => requestBlob(`/api/v1/ordenes-servicio/${orderId}/documentos/${documentId}`),
  deleteOrderDocument: (orderId: number, documentId: number) => request<void>(`/api/v1/ordenes-servicio/${orderId}/documentos/${documentId}`, { method: 'DELETE' }),
}
