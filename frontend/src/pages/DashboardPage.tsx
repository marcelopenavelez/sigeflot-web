import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { VehicleList } from '../types/api'
const states = [['Total de vehículos', 'total', 'bg-slate-800'], ['Operativos', 'OPERATIVO', 'bg-emerald-600'], ['En mantenimiento', 'MANTENIMIENTO', 'bg-amber-500'], ['Inactivos', 'INACTIVO', 'bg-slate-500']] as const
export function DashboardPage() {
  const [data, setData] = useState<VehicleList | null>(null); const [error, setError] = useState('')
  useEffect(() => { api.vehicles(new URLSearchParams({ page_size: '100' })).then(setData).catch(() => setError('No fue posible cargar el resumen de vehículos.')) }, [])
  if (error) return <p className="rounded-lg bg-red-50 p-4 text-red-700">{error}</p>
  if (!data) return <p className="text-slate-500">Cargando resumen…</p>
  return <><div className="mb-7"><p className="text-sm font-semibold uppercase tracking-wider text-cyan-700">Panel principal</p><h2 className="mt-1 text-2xl font-bold text-slate-950">Resumen de la flota</h2><p className="mt-2 text-slate-600">Estado actual de los vehículos registrados.</p></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{states.map(([label, value, color]) => { const count = value === 'total' ? data.total : data.items.filter(item => item.estado === value).length; return <article key={value} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className={`h-1.5 w-12 rounded ${color}`} /><p className="mt-5 text-sm text-slate-500">{label}</p><p className="mt-1 text-3xl font-bold text-slate-950">{count}</p></article> })}</div><p className="mt-5 text-sm text-slate-500">El resumen se calcula con los primeros 100 registros disponibles.</p></>
}
