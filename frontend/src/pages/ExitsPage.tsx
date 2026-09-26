import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import type { ExitVehicle } from '../types/api'

const fmt = (date: Date, options: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat('es-PE', options).format(date)

function ReadOnly({ label, value }: { label: string; value: string }) {
  return <label className="block text-sm font-semibold text-slate-700">{label}<output className="mt-1 flex min-h-11 items-center rounded-lg border border-slate-200 bg-slate-50 px-3 font-normal">{value}</output></label>
}

export function ExitsPage() {
  const { user } = useAuth()
  const [vehicles, setVehicles] = useState<ExitVehicle[]>([])
  const [vehicleId, setVehicleId] = useState('')
  const [kilometraje, setKilometraje] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [saving, setSaving] = useState(false)
  const [now, setNow] = useState(() => new Date())
  const selected = vehicles.find(item => item.id === Number(vehicleId))
  const currentKilometraje = selected?.kilometraje_actual
  const hasRegisteredKilometraje = currentKilometraje !== null && currentKilometraje !== undefined

  const load = async () => {
    try { setVehicles(await api.availableExitVehicles()) }
    catch (err) { setError(err instanceof ApiError ? err.message : 'No se pudieron cargar los vehículos disponibles.') }
  }

  useEffect(() => { queueMicrotask(() => { void load() }) }, [])
  useEffect(() => {
    const interval = window.setInterval(() => setNow(new Date()), 30_000)
    return () => window.clearInterval(interval)
  }, [])

  const reset = () => { setVehicleId(''); setKilometraje(''); setObservaciones(''); setError('') }

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setNotice('')
    const km = Number(kilometraje)
    if (!selected) return setError('Seleccione un vehículo.')
    if (currentKilometraje === null || currentKilometraje === undefined) return setError('El vehículo no tiene kilometraje registrado y no puede registrar una salida.')
    if (!Number.isInteger(km) || km < currentKilometraje) return setError('Ingrese un kilometraje igual o mayor al actual.')
    setSaving(true)
    try {
      await api.createExit({ vehiculo_id: selected.id, kilometraje_salida: km, observaciones })
      setNotice('Salida registrada correctamente.'); reset(); await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.status === 409 ? 'Este vehículo ya tiene una salida abierta.' : err.status === 401 ? 'Su sesión expiró. Inicie sesión nuevamente.' : err.status === 403 ? 'No tiene permisos para registrar salidas.' : err.message : 'No fue posible registrar la salida.')
    } finally { setSaving(false) }
  }

  const kilometrajeLabel = !selected ? 'Seleccione un vehículo' : currentKilometraje === null || currentKilometraje === undefined ? 'Sin kilometraje registrado' : `${currentKilometraje.toLocaleString('es-PE')} km`
  return <div className="mx-auto max-w-4xl"><div className="mb-5"><p className="text-sm font-semibold uppercase tracking-wider text-cyan-700">Operación móvil</p><h2 className="mt-1 text-2xl font-bold text-slate-950">Registro de Salida Vehicular</h2><p className="mt-2 text-slate-600">Registre la salida en pocos pasos.</p></div><section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-cyan-800 bg-cyan-700 px-5 py-4 text-white"><h3 className="font-bold">Nueva salida</h3></div><form onSubmit={submit} className="grid gap-5 p-5 sm:p-7"><div className="grid gap-4 sm:grid-cols-2"><ReadOnly label="Chofer" value={`${user?.nombres ?? ''} ${user?.apellidos ?? ''}`} /><ReadOnly label="Fecha" value={fmt(now, { dateStyle: 'long' })} /><ReadOnly label="Hora" value={fmt(now, { timeStyle: 'short' })} /></div><p className="-mt-3 text-xs text-slate-500">La fecha y hora son informativas; el servidor registra la hora oficial de salida.</p><label className="block text-sm font-semibold text-slate-700">Vehículo<select required value={vehicleId} onChange={event => { setVehicleId(event.target.value); setKilometraje('') }} className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 outline-none focus:border-cyan-600"><option value="">Seleccione un vehículo</option>{vehicles.map(vehicle => <option key={vehicle.id} value={vehicle.id}>{vehicle.placa}{vehicle.marca || vehicle.modelo ? ` · ${[vehicle.marca, vehicle.modelo].filter(Boolean).join(' ')}` : ''}</option>)}</select></label><div className="grid gap-4 sm:grid-cols-2"><ReadOnly label="Kilometraje actual" value={kilometrajeLabel} /><label className="block text-sm font-semibold text-slate-700">Kilometraje de salida<input required disabled={Boolean(selected) && !hasRegisteredKilometraje} inputMode="numeric" min={currentKilometraje ?? undefined} type="number" value={kilometraje} onChange={event => setKilometraje(event.target.value)} placeholder={hasRegisteredKilometraje ? 'Ingrese el kilometraje' : 'Requiere kilometraje registrado'} className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 px-3 outline-none focus:border-cyan-600 disabled:cursor-not-allowed disabled:bg-slate-100" /></label></div>{selected && !hasRegisteredKilometraje && <p role="alert" className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">Sin kilometraje registrado. Actualice el vehículo antes de registrar una salida.</p>}<label className="block text-sm font-semibold text-slate-700">Observaciones <span className="font-normal text-slate-500">(opcional)</span><textarea value={observaciones} onChange={event => setObservaciones(event.target.value)} rows={4} placeholder="Ingrese observaciones del viaje" className="mt-1 min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600" /></label>{error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}{notice && <p role="status" className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}<div className="grid grid-cols-1 gap-3 pt-1 sm:flex sm:justify-end"><button type="button" onClick={reset} className="min-h-11 rounded-lg border border-slate-300 px-5 font-semibold">Cancelar</button><button disabled={saving || (Boolean(selected) && !hasRegisteredKilometraje)} className="min-h-11 rounded-lg bg-cyan-700 px-5 font-semibold text-white disabled:opacity-60">{saving ? 'Registrando…' : 'Registrar salida'}</button></div></form></section></div>
}
