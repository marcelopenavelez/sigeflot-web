import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { ApiError, api } from '../services/api'
import type { OrderAuditResponse, OrderDetail, OrderDocumentCategory, OrderDocumentItem } from '../types/api'

const MAX_FILE_SIZE = 10 * 1024 * 1024
const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']
const CATEGORY_LABELS: Record<OrderDocumentCategory, string> = {
  ORDEN_SERVICIO: 'Orden de servicio',
  FACTURA: 'Factura',
  INFORME_TECNICO: 'Informe técnico',
  FOTOGRAFIA: 'Fotografía',
  OTRO: 'Otro',
}

const show = (value: unknown) => value === null || value === undefined || value === '' ? '—' : String(value)
const errorMessage = (error: unknown, fallback: string) => error instanceof ApiError ? error.message : fallback
const formatBytes = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function OrderDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const orderId = Number(id)
  const fileInput = useRef<HTMLInputElement>(null)
  const [order, setOrder] = useState<OrderDetail | null>(null)
  const [audit, setAudit] = useState<OrderAuditResponse>([])
  const [documents, setDocuments] = useState<OrderDocumentItem[]>([])
  const [error, setError] = useState('')
  const [documentError, setDocumentError] = useState('')
  const [documentsLoading, setDocumentsLoading] = useState(true)
  const [confirmClose, setConfirmClose] = useState(false)
  const [closing, setClosing] = useState(false)
  const [category, setCategory] = useState<OrderDocumentCategory | ''>('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [uploadMessage, setUploadMessage] = useState('')
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [documentToDelete, setDocumentToDelete] = useState<OrderDocumentItem | null>(null)
  const [deleting, setDeleting] = useState(false)

  const canReadDocuments = ['ADMINISTRADOR', 'MECANICO', 'CONSULTA'].includes(user?.rol || '')
  const canUploadDocuments = ['ADMINISTRADOR', 'MECANICO'].includes(user?.rol || '')
  const canDeleteDocuments = user?.rol === 'ADMINISTRADOR'

  const loadOrderData = () => {
    if (!Number.isInteger(orderId) || orderId <= 0) return
    api.getOrder(orderId).then(setOrder).catch((requestError) => setError(errorMessage(requestError, 'No se pudo cargar la orden.')))
    api.getOrderAudit(orderId).then(setAudit).catch(() => setAudit([]))
  }

  const loadDocuments = () => {
    if (!canReadDocuments || !Number.isInteger(orderId) || orderId <= 0) return
    setDocumentsLoading(true)
    setDocumentError('')
    api.listOrderDocuments(orderId)
      .then(setDocuments)
      .catch((requestError) => setDocumentError(errorMessage(requestError, 'No se pudieron cargar los documentos.')))
      .finally(() => setDocumentsLoading(false))
  }

  useEffect(() => {
    queueMicrotask(() => {
      loadOrderData()
      loadDocuments()
    })
    // These loaders intentionally rerun only when the route or authenticated role changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderId, user?.rol])

  if (error) return <p role="alert" className="rounded-lg bg-red-50 p-4 text-red-700">{error}</p>
  if (!order) return <p>Cargando orden…</p>

  const canMutateOrder = !order.es_historico && ['ADMINISTRADOR', 'MECANICO'].includes(user?.rol || '')
  const editable = canMutateOrder && order.estado === 'ABIERTA'

  const closeOrder = async () => {
    setClosing(true)
    try {
      await api.closeOrder(order.id)
      setConfirmClose(false)
      loadOrderData()
    } catch (requestError) {
      setError(errorMessage(requestError, 'No se pudo cerrar la orden.'))
    } finally {
      setClosing(false)
    }
  }

  const uploadDocument = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setUploadMessage('')
    if (!category) {
      setUploadState('error'); setUploadMessage('Seleccione una categoría.'); return
    }
    if (!selectedFile) {
      setUploadState('error'); setUploadMessage('Seleccione un archivo.'); return
    }
    const extension = selectedFile.name.includes('.') ? selectedFile.name.slice(selectedFile.name.lastIndexOf('.')).toLowerCase() : ''
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setUploadState('error'); setUploadMessage('Solo se permiten archivos PDF, JPG, JPEG o PNG.'); return
    }
    if (selectedFile.size > MAX_FILE_SIZE) {
      setUploadState('error'); setUploadMessage('El archivo supera el máximo de 10 MB.'); return
    }
    setUploadState('uploading')
    try {
      await api.uploadOrderDocument(order.id, selectedFile, category)
      setSelectedFile(null)
      setCategory('')
      if (fileInput.current) fileInput.current.value = ''
      setUploadState('success')
      setUploadMessage('Documento adjuntado correctamente.')
      loadDocuments()
      loadOrderData()
    } catch (requestError) {
      setUploadState('error')
      setUploadMessage(errorMessage(requestError, 'No se pudo adjuntar el documento.'))
    }
  }

  const downloadDocument = async (document: OrderDocumentItem) => {
    setDownloadingId(document.id)
    setDocumentError('')
    try {
      const blob = await api.downloadOrderDocument(order.id, document.id)
      const objectUrl = URL.createObjectURL(blob)
      const link = window.document.createElement('a')
      link.href = objectUrl
      link.download = document.nombre_original
      window.document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
    } catch (requestError) {
      setDocumentError(errorMessage(requestError, 'No se pudo descargar el documento.'))
    } finally {
      setDownloadingId(null)
    }
  }

  const deleteDocument = async () => {
    if (!documentToDelete) return
    setDeleting(true)
    setDocumentError('')
    try {
      await api.deleteOrderDocument(order.id, documentToDelete.id)
      setDocumentToDelete(null)
      loadDocuments()
      loadOrderData()
    } catch (requestError) {
      setDocumentError(errorMessage(requestError, 'No se pudo retirar el documento.'))
    } finally {
      setDeleting(false)
    }
  }

  return <div className="mx-auto max-w-4xl">
    <Link to="/ordenes" className="inline-flex min-h-11 items-center text-cyan-700">← Volver a Órdenes</Link>
    <h2 className="mt-3 text-2xl font-bold">Orden {order.numero_orden}</h2>
    {order.es_historico && <p className="mt-2 rounded bg-slate-100 p-3">Histórica - solo lectura de datos</p>}
    <p className="mt-2">Estado: <b>{order.estado}</b></p>
    {editable && <div className="mt-3 flex flex-col gap-2 sm:flex-row">
      <Link to={`/ordenes/${order.id}/editar`} className="min-h-11 rounded bg-cyan-700 px-4 py-3 text-center text-white">Editar Orden</Link>
      <button onClick={() => setConfirmClose(true)} className="min-h-11 rounded border px-4">Cerrar Orden</button>
    </div>}

    <section className="mt-5 rounded-xl bg-white p-5">
      <h3 className="font-bold">Estado de archivo</h3>
      {canMutateOrder ? <select value={order.estado_archivo || 'PENDIENTE'} onChange={async (event) => { await api.updateOrderArchive(order.id, { estado_archivo: event.target.value as 'PENDIENTE' | 'ARCHIVADO' }); loadOrderData() }} className="mt-2 min-h-11 border p-2"><option>PENDIENTE</option><option>ARCHIVADO</option></select> : <p>{show(order.estado_archivo)}</p>}
    </section>

    <section className="mt-5 rounded-xl bg-white p-5">
      <p>Fecha: {show(order.fecha)} · Placa: {show(order.placa)} · Kilometraje: {show(order.kilometraje_orden)}</p>
      <p>Proveedor: {show(order.proveedor)}</p>
      <p>Correctivo: {show(order.descripcion_correctivo)}</p>
    </section>

    {canReadDocuments && <section className="mt-5 rounded-xl bg-white p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-bold">Documentos y evidencias</h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">{documents.length} adjunto{documents.length === 1 ? '' : 's'}</span>
      </div>

      {canUploadDocuments && <form onSubmit={uploadDocument} className="mt-4 grid gap-3 rounded-lg border border-slate-200 p-4 sm:grid-cols-2">
        <label className="text-sm font-medium">Categoría
          <select value={category} onChange={(event) => setCategory(event.target.value as OrderDocumentCategory | '')} className="mt-1 min-h-11 w-full rounded border border-slate-300 p-2">
            <option value="">Seleccione una categoría</option>
            {Object.entries(CATEGORY_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label className="text-sm font-medium">Archivo
          <input ref={fileInput} type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(event) => { setSelectedFile(event.target.files?.[0] || null); setUploadState('idle'); setUploadMessage('') }} className="mt-1 min-h-11 w-full rounded border border-slate-300 p-2" />
        </label>
        <div className="sm:col-span-2">
          <p className="text-xs text-slate-500">PDF, JPG, JPEG o PNG. Máximo 10 MB.</p>
          {uploadMessage && <p role={uploadState === 'error' ? 'alert' : 'status'} className={`mt-2 text-sm ${uploadState === 'error' ? 'text-red-700' : 'text-emerald-700'}`}>{uploadMessage}</p>}
          <button disabled={uploadState === 'uploading'} className="mt-3 min-h-11 w-full rounded bg-cyan-700 px-4 text-white disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto">{uploadState === 'uploading' ? 'Subiendo...' : 'Adjuntar documento'}</button>
        </div>
      </form>}

      {documentError && <p role="alert" className="mt-4 rounded bg-red-50 p-3 text-sm text-red-700">{documentError}</p>}
      {documentsLoading ? <p className="mt-4 text-slate-600">Cargando documentos…</p> : documents.length === 0 ? <p className="mt-4 rounded bg-slate-50 p-4 text-slate-600">No hay documentos o evidencias adjuntas.</p> : <div className="mt-4 grid gap-3">
        {documents.map((document) => <article key={document.id} className="min-w-0 rounded-lg border border-slate-200 p-4">
          <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <p className="break-words font-semibold text-slate-900">{document.nombre_original}</p>
              <p className="mt-1 text-sm text-slate-600">{CATEGORY_LABELS[document.categoria]} · {document.extension.toUpperCase().replace('.', '')} · {formatBytes(document.tamano_bytes)}</p>
              <p className="mt-1 text-sm text-slate-500">{new Date(document.fecha_subida).toLocaleString('es-PE')} · {document.usuario}</p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <button disabled={downloadingId === document.id} onClick={() => downloadDocument(document)} className="min-h-11 rounded border border-cyan-700 px-4 text-cyan-700 disabled:opacity-60">{downloadingId === document.id ? 'Descargando...' : 'Ver/Descargar'}</button>
              {canDeleteDocuments && <button onClick={() => setDocumentToDelete(document)} className="min-h-11 rounded border border-red-300 px-4 text-red-700">Eliminar</button>}
            </div>
          </div>
        </article>)}
      </div>}
    </section>}

    <section className="mt-5 rounded-xl bg-white p-5">
      <h3 className="font-bold">Historial de cambios</h3>
      {audit.length ? audit.map((item) => <article key={`${item.accion}-${item.fecha_hora}`} className="border-b py-3"><b>{item.accion}</b><p>{new Date(item.fecha_hora).toLocaleString('es-PE')} · {item.usuario}</p>{Object.entries(item.cambios).map(([key, change]) => <p key={key}>{key}: {show(change.antes)} → {show(change.despues)}</p>)}</article>) : <p>No existen cambios operativos registrados.</p>}
    </section>

    {confirmClose && <div className="fixed inset-0 z-40 grid place-items-center bg-slate-950/50 p-4"><div className="w-full max-w-md rounded-xl bg-white p-6"><h3 className="font-bold">¿Confirmar cierre de la orden?</h3><p className="mt-2">Una orden cerrada no podrá editarse en esta fase.</p><div className="mt-4 flex justify-end gap-2"><button onClick={() => setConfirmClose(false)} className="min-h-11 px-4">Cancelar</button><button disabled={closing} onClick={closeOrder} className="min-h-11 rounded bg-cyan-700 px-4 text-white">Confirmar cierre</button></div></div></div>}

    {documentToDelete && <div className="fixed inset-0 z-40 grid place-items-center bg-slate-950/50 p-4"><div className="w-full max-w-md rounded-xl bg-white p-6"><h3 className="font-bold">¿Retirar este documento de la orden?</h3><p className="mt-2 break-words">{documentToDelete.nombre_original}</p><p className="mt-2 text-sm text-slate-600">El documento dejará de estar disponible en SIGEFLOT, pero se conservará para trazabilidad.</p><div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end"><button disabled={deleting} onClick={() => setDocumentToDelete(null)} className="min-h-11 px-4">Cancelar</button><button disabled={deleting} onClick={deleteDocument} className="min-h-11 rounded bg-red-700 px-4 text-white disabled:opacity-60">{deleting ? 'Retirando...' : 'Retirar documento'}</button></div></div></div>}
  </div>
}
