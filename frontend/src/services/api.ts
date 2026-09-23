import type { User, Vehicle, VehicleList, VehiclePayload } from '../types/api'

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
  if (options.body) headers.set('Content-Type', 'application/json')
  const token = getToken(); if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (response.status === 204) return undefined as T
  const body = await response.json().catch(() => ({})) as { detail?: string }
  if (!response.ok) throw new ApiError(response.status, body.detail || 'No fue posible completar la operación.')
  return body as T
}
export const api = {
  login: (email: string, password: string) => request<{ access_token: string }>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request<User>('/api/v1/auth/me'),
  vehicles: (params = new URLSearchParams()) => request<VehicleList>(`/api/v1/vehicles?${params}`),
  createVehicle: (payload: Partial<VehiclePayload>) => request<Vehicle>('/api/v1/vehicles', { method: 'POST', body: JSON.stringify(payload) }),
  updateVehicle: (id: number, payload: Partial<VehiclePayload>) => request<Vehicle>(`/api/v1/vehicles/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deactivateVehicle: (id: number) => request<void>(`/api/v1/vehicles/${id}`, { method: 'DELETE' }),
}
