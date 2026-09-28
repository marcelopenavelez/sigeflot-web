import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, api } from '../services/api'
import type { MaintenanceCatalogItem, OrderProvider, OrderVehicle } from '../types/api'

const formatDate = (date: Date) => new Intl.DateTimeFormat('es-PE', { dateStyle: 'long' }).format(date)

function ReadOnly({ label, value }: { label: string; value: string }) {
  return <label className="block text-sm font-semibold text-slate-700">{label}<output className="mt-1 flex min-h-11 items-center rounded-lg border border-slate-200 bg-slate-50 px-3 font-normal text-slate-700">{value}</output></label>
}

export function NewOrderPage() {
  const [vehicles, setVehicles] = useState<OrderVehicle[]>([])
  const [providers, setProviders] = useState<OrderProvider[]>([])
  const [catalog, setCatalog] = useState<MaintenanceCatalogItem[]>([])
  const [numeroOrden, setNumeroOrden] = useState('')
  const [vehicleId, setVehicleId] = useState('')
  const [kilometraje, setKilometraje] = useState('')
  const [providerId, setProviderId] = useState('')
  const [estadoArchivo, setEstadoArchivo] = useState<'PENDIENTE' | 'ARCHIVADO'>('PENDIENTE')
  const [correctivo, setCorrectivo] = useState('')
  const [search, setSearch] = useState('')
  const [selectedIds, setSelectedIds] = useState<Set<number>>(() => new Set())
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [saving, setSaving] = useState(false)
  const [loadingCatalog, setLoadingCatalog] = useState(false)
  const selectedVehicle = useMemo(() => vehicles.find(vehicle => vehicle.id === Number(vehicleId)), [vehicles, vehicleId])
  const currentKilometraje = selectedVehicle?.kilometraje_actual

  const loadAuxiliaries = async () => {
    try {
      const [loadedVehicles, loadedProviders] = await Promise.all([api.orderVehicles(), api.orderProviders()])
      setVehicles(loadedVehicles); setProviders(loadedProviders)
    } catch (err) { setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los datos de la orden.') }
  }

  useEffect(() => { queueMicrotask(() => { void loadAuxiliaries() }) }, [])
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoadingCatalog(true)
      api.maintenanceCatalog(search.trim()).then(setCatalog).catch(err => setError(err instanceof ApiError ? err.message : 'No se pudo cargar el catálogo de mantenimiento.')).finally(() => setLoadingCatalog(false))
    }, 250)
    return () => window.clearTimeout(timer)
  }, [search])

  const reset = () => {
    setNumeroOrden(''); setVehicleId(''); setKilometraje(''); setProviderId(''); setEstadoArchivo('PENDIENTE'); setCorrectivo(''); setSearch(''); setSelectedIds(new Set()); setError('')
  }
  const togglePreventive = (id: number) => setSelectedIds(current => {
    const next = new Set(current)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    return next
  })
  const selectVisible = () => setSelectedIds(current => new Set([...current, ...catalog.map(item => item.id)]))
  const clearSelected = () => setSelectedIds(new Set())

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setNotice('')
    const normalizedNumber = numeroOrden.trim()
    const orderKilometraje = Number(kilometraje)
    const normalizedCorrective = correctivo.trim()
    if (!normalizedNumber) return setError('Ingrese el número de orden de logística.')
    if (!selectedVehicle) return setError('Seleccione un vehículo.')
    if (!Number.isInteger(orderKilometraje) || orderKilometraje < 0) return setError('Ingrese un kilometraje de orden válido.')
    if (currentKilometraje !== null && currentKilometraje !== undefined && orderKilometraje < currentKilometraje) return setError('El kilometraje de la orden no puede ser menor al actual.')
    if (selectedIds.size === 0 && !normalizedCorrective) return setError('Seleccione un preventivo o ingrese trabajos correctivos.')
    setSaving(true)
    try {
      const created = await api.createOrder({ numero_orden: normalizedNumber, vehiculo_id: selectedVehicle.id, kilometraje_orden: orderKilometraje, preventivo_ids: [...selectedIds], descripcion_correctivo: normalizedCorrective || null, proveedor_id: providerId ? Number(providerId) : null, estado_archivo: estadoArchivo })
      reset(); setNotice(`Orden de servicio ${created.numero_orden} registrada correctamente.`); await loadAuxiliaries()
    } catch (err) {
      if (!(err instanceof ApiError)) setError('No fue posible registrar la orden de servicio.')
      else if (err.status === 401) setError('Su sesión expiró. Inicie sesión nuevamente.')
      else if (err.status === 403) setError('No tiene permisos para crear órdenes de servicio.')
      else if (err.status === 409) setError('El número de orden ya está registrado.')
      else if (err.status === 404 || err.status === 422) setError(err.message)
      else setError('No fue posible registrar la orden de servicio.')
    } finally { setSaving(false) }
  }

  const kilometrajeActual = !selectedVehicle ? 'Seleccione un vehículo' : currentKilometraje === null || currentKilometraje === undefined ? 'Sin kilometraje registrado' : `${currentKilometraje.toLocaleString('es-PE')} km`
  return <div className="mx-auto max-w-5xl"><div className="mb-6"><p className="text-sm font-semibold uppercase tracking-wider text-cyan-700">Mantenimiento</p><h2 className="mt-1 text-2xl font-bold text-slate-950">Crear Orden de Servicio</h2><p className="mt-2 text-slate-600">Registre las tareas preventivas y correctivas de la unidad.</p></div><form onSubmit={submit} className="grid gap-5"><section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7"><h3 className="font-bold text-slate-900">1. Datos de la orden</h3><div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"><label className="block text-sm font-semibold text-slate-700">ID / Número de Orden de Logística<input required maxLength={40} value={numeroOrden} onChange={event => setNumeroOrden(event.target.value)} placeholder="Ejemplo: 622-2026" className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 px-3 outline-none focus:border-cyan-600" /></label><ReadOnly label="Fecha de registro" value={formatDate(new Date())} /><label className="block text-sm font-semibold text-slate-700">Estado de Archivo<select value={estadoArchivo} onChange={event => setEstadoArchivo(event.target.value as 'PENDIENTE' | 'ARCHIVADO')} className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 outline-none focus:border-cyan-600"><option value="PENDIENTE">PENDIENTE</option><option value="ARCHIVADO">ARCHIVADO</option></select></label></div><p className="mt-3 text-xs text-slate-500">La fecha oficial de la orden la genera el servidor.</p></section><section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7"><h3 className="font-bold text-slate-900">2. Datos del vehículo</h3><div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"><label className="block text-sm font-semibold text-slate-700">Vehículo<select required value={vehicleId} onChange={event => { setVehicleId(event.target.value); setKilometraje('') }} className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 outline-none focus:border-cyan-600"><option value="">Seleccione un vehículo</option>{vehicles.map(vehicle => <option key={vehicle.id} value={vehicle.id}>{vehicle.placa}{vehicle.marca || vehicle.modelo ? ` · ${[vehicle.marca, vehicle.modelo].filter(Boolean).join(' ')}` : ''}</option>)}</select></label><ReadOnly label="Kilometraje actual" value={kilometrajeActual} /><label className="block text-sm font-semibold text-slate-700">Kilometraje de la orden<input required inputMode="numeric" min={currentKilometraje ?? 0} type="number" value={kilometraje} onChange={event => setKilometraje(event.target.value)} placeholder="Ingrese el kilometraje" className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 px-3 outline-none focus:border-cyan-600" /></label></div><label className="mt-4 block max-w-xl text-sm font-semibold text-slate-700">Proveedor / Taller <span className="font-normal text-slate-500">(opcional)</span><select value={providerId} onChange={event => setProviderId(event.target.value)} className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 outline-none focus:border-cyan-600"><option value="">Sin proveedor registrado</option>{providers.map(provider => <option key={provider.id} value={provider.id}>{provider.razon_social}{provider.nombre_comercial ? ` · ${provider.nombre_comercial}` : ''}</option>)}</select></label></section><section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7"><div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><h3 className="font-bold text-slate-900">3. Mantenimiento Preventivo</h3><p className="text-sm text-slate-600">{selectedIds.size} seleccionado(s)</p></div><div className="flex flex-col gap-2 sm:flex-row"><button type="button" onClick={selectVisible} disabled={catalog.length === 0} className="min-h-11 rounded-lg border border-cyan-700 px-4 text-sm font-semibold text-cyan-800 disabled:opacity-50">Seleccionar visibles</button><button type="button" onClick={clearSelected} disabled={selectedIds.size === 0} className="min-h-11 rounded-lg border border-slate-300 px-4 text-sm font-semibold disabled:opacity-50">Limpiar selección</button></div></div><label className="mt-4 block text-sm font-semibold text-slate-700">Buscar componente o tarea<input value={search} onChange={event => setSearch(event.target.value)} placeholder="Filtrar catálogo" className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 px-3 outline-none focus:border-cyan-600" /></label><div className="mt-3 max-h-80 overflow-y-auto rounded-lg border border-slate-200" aria-busy={loadingCatalog}>{loadingCatalog ? <p className="p-4 text-sm text-slate-500">Cargando catálogo…</p> : catalog.length === 0 ? <p className="p-4 text-sm text-slate-500">No hay tareas para este filtro.</p> : catalog.map(item => <label key={item.id} className="flex min-h-11 cursor-pointer items-start gap-3 border-b border-slate-100 px-3 py-3 last:border-0 hover:bg-slate-50"><input type="checkbox" checked={selectedIds.has(item.id)} onChange={() => togglePreventive(item.id)} className="mt-1 h-4 w-4 accent-cyan-700" /><span className="min-w-0"><span className="block text-sm font-medium text-slate-800">{item.tarea}</span>{(item.prioridad || item.intervalo_km || item.intervalo_dias) && <span className="block text-xs text-slate-500">{item.prioridad ? `Prioridad: ${item.prioridad}` : ''}{item.intervalo_km ? `${item.prioridad ? ' · ' : ''}${item.intervalo_km.toLocaleString('es-PE')} km` : ''}{item.intervalo_dias ? `${item.prioridad || item.intervalo_km ? ' · ' : ''}${item.intervalo_dias} días` : ''}</span>}</span></label>)}</div></section><section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7"><h3 className="font-bold text-slate-900">4. Mantenimiento Correctivo</h3><label className="mt-4 block text-sm font-semibold text-slate-700">Trabajos correctivos <span className="font-normal text-slate-500">(requerido si no selecciona preventivos)</span><textarea maxLength={5000} value={correctivo} onChange={event => setCorrectivo(event.target.value)} rows={5} placeholder="Ejemplo: reparación de arrancador, soldadura de muelle" className="mt-1 min-h-28 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600" /></label></section>{error && <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</p>}{notice && <p role="status" className="rounded-lg bg-emerald-50 p-4 text-sm text-emerald-800">{notice}</p>}<div className="grid grid-cols-1 gap-3 sm:flex sm:justify-end"><button type="button" onClick={reset} className="min-h-11 rounded-lg border border-slate-300 px-5 font-semibold">Cancelar</button><button disabled={saving} className="min-h-11 rounded-lg bg-cyan-700 px-5 font-semibold text-white disabled:opacity-60">{saving ? 'Registrando…' : 'Registrar orden'}</button></div></form></div>
}
