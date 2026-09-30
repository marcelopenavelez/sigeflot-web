from datetime import datetime, timedelta, timezone
from pathlib import PurePath
from tempfile import SpooledTemporaryFile
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.background import BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.auth import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models import OrdenServicio, OrdenServicioAuditoria, OrdenServicioDocumento, Usuario
from app.schemas.order_document import OrderDocumentRead
from app.services.storage import StorageBackend, StorageError, get_storage


router = APIRouter(prefix="/api/v1/ordenes-servicio", tags=["ordenes-servicio-documentos"])
LIMA = timezone(timedelta(hours=-5), name="America/Lima")
UPLOAD_ROLES = {"ADMINISTRADOR", "MECANICO"}
READ_ROLES = {"ADMINISTRADOR", "MECANICO", "CONSULTA"}
CATEGORIES = {"ORDEN_SERVICIO", "FACTURA", "INFORME_TECNICO", "FOTOGRAFIA", "OTRO"}
MIME_EXTENSIONS = {
    "application/pdf": {".pdf"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
}
EXECUTABLE_SUFFIXES = {".exe", ".com", ".bat", ".cmd", ".ps1", ".sh", ".js", ".html", ".php"}


def require_role(user: Usuario, allowed: set[str]) -> None:
    if user.rol.codigo not in allowed:
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar documentos de órdenes")


def get_order(db: Session, order_id: int) -> OrdenServicio:
    order = db.get(OrdenServicio, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Orden de servicio no encontrada")
    return order


def safe_original_name(filename: str | None) -> tuple[str, str]:
    normalized = (filename or "").replace("\\", "/")
    name = PurePath(normalized).name.strip().replace("\r", "").replace("\n", "")
    if not name or name in {".", ".."} or len(name) > 255:
        raise HTTPException(status_code=422, detail="Nombre de archivo inválido")
    suffixes = [suffix.lower() for suffix in PurePath(name).suffixes]
    if not suffixes or any(suffix in EXECUTABLE_SUFFIXES for suffix in suffixes[:-1]):
        raise HTTPException(status_code=422, detail="Extensión de archivo no permitida")
    return name, suffixes[-1]


def signature_matches(content_type: str, header: bytes) -> bool:
    if content_type == "application/pdf":
        return header.startswith(b"%PDF-")
    if content_type == "image/jpeg":
        return header.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    return False


def validate_upload(file: UploadFile) -> tuple[SpooledTemporaryFile, str, str, int]:
    name, extension = safe_original_name(file.filename)
    content_type = (file.content_type or "").lower().strip()
    if content_type not in MIME_EXTENSIONS or extension not in MIME_EXTENSIONS[content_type]:
        raise HTTPException(status_code=422, detail="Tipo MIME o extensión no permitidos")
    maximum = get_settings().storage_max_file_size_bytes
    temporary = SpooledTemporaryFile(max_size=min(maximum, 1024 * 1024), mode="w+b")
    size = 0
    header = b""
    try:
        while chunk := file.file.read(64 * 1024):
            size += len(chunk)
            if size > maximum:
                raise HTTPException(status_code=413, detail="El archivo supera el tamaño máximo permitido")
            if len(header) < 16:
                header += chunk[:16 - len(header)]
            temporary.write(chunk)
        if size == 0:
            raise HTTPException(status_code=422, detail="El archivo está vacío")
        if not signature_matches(content_type, header):
            raise HTTPException(status_code=422, detail="El contenido no coincide con el tipo de archivo declarado")
        temporary.seek(0)
        return temporary, name, extension, size
    except Exception:
        temporary.close()
        raise


def audit_changes(document: OrdenServicioDocumento) -> dict:
    values = {
        "documento_id": document.id,
        "nombre_original": document.nombre_original,
        "categoria": document.categoria,
        "tipo_mime": document.tipo_mime,
        "tamano_bytes": document.tamano_bytes,
    }
    return {key: {"antes": None, "despues": value} for key, value in values.items()}


def document_read(document: OrdenServicioDocumento) -> OrderDocumentRead:
    user = document.usuario_subida
    return OrderDocumentRead(
        id=document.id,
        nombre_original=document.nombre_original,
        tipo_mime=document.tipo_mime,
        extension=document.extension,
        tamano_bytes=document.tamano_bytes,
        categoria=document.categoria,
        fecha_subida=document.fecha_subida,
        usuario=f"{user.nombres} {user.apellidos}",
        activo=document.activo,
    )


@router.post("/{order_id}/documentos", response_model=OrderDocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(order_id: int, categoria: str = Form(...), file: UploadFile = File(...),
                    db: Session = Depends(get_db), user: Usuario = Depends(get_current_user),
                    storage: StorageBackend = Depends(get_storage)) -> OrderDocumentRead:
    require_role(user, UPLOAD_ROLES)
    order = get_order(db, order_id)
    category = categoria.strip().upper()
    if category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Categoría documental inválida")
    temporary, original_name, extension, size = validate_upload(file)
    identifier = uuid4()
    stored_name = f"{identifier}{extension}"
    prefix = get_settings().storage_prefix.strip("/") or "ordenes"
    storage_key = f"{prefix}/{order.id}/{stored_name}"
    try:
        storage.save(storage_key, temporary, file.content_type or "application/octet-stream")
    except StorageError as error:
        raise HTTPException(status_code=503, detail="No fue posible almacenar el documento") from error
    finally:
        temporary.close()

    document = OrdenServicioDocumento(
        orden_servicio_id=order.id,
        nombre_original=original_name,
        nombre_almacenado=stored_name,
        tipo_mime=file.content_type or "application/octet-stream",
        extension=extension,
        tamano_bytes=size,
        categoria=category,
        storage_key=storage_key,
        fecha_subida=datetime.now(LIMA),
        usuario_subida_id=user.id,
        activo=True,
    )
    try:
        db.add(document)
        db.flush()
        db.add(OrdenServicioAuditoria(
            orden_servicio_id=order.id,
            usuario_id=user.id,
            accion="DOCUMENTO_ADJUNTADO",
            fecha_hora=datetime.now(LIMA),
            cambios=audit_changes(document),
        ))
        db.commit()
        db.refresh(document)
        document.usuario_subida = user
        return document_read(document)
    except Exception as error:
        db.rollback()
        try:
            storage.delete(storage_key)
        except StorageError:
            pass
        raise HTTPException(status_code=500, detail="No fue posible registrar el documento") from error


@router.get("/{order_id}/documentos", response_model=list[OrderDocumentRead])
def list_documents(order_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> list[OrderDocumentRead]:
    require_role(user, READ_ROLES)
    get_order(db, order_id)
    documents = db.scalars(
        select(OrdenServicioDocumento)
        .options(selectinload(OrdenServicioDocumento.usuario_subida))
        .where(OrdenServicioDocumento.orden_servicio_id == order_id, OrdenServicioDocumento.activo.is_(True))
        .order_by(OrdenServicioDocumento.fecha_subida.desc(), OrdenServicioDocumento.id.desc())
    ).all()
    return [document_read(document) for document in documents]


@router.get("/{order_id}/documentos/{document_id}")
def download_document(order_id: int, document_id: int, background_tasks: BackgroundTasks,
                      db: Session = Depends(get_db), user: Usuario = Depends(get_current_user),
                      storage: StorageBackend = Depends(get_storage)) -> StreamingResponse:
    require_role(user, READ_ROLES)
    get_order(db, order_id)
    document = db.scalar(select(OrdenServicioDocumento).where(
        OrdenServicioDocumento.id == document_id,
        OrdenServicioDocumento.orden_servicio_id == order_id,
        OrdenServicioDocumento.activo.is_(True),
    ))
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    try:
        stream = storage.open(document.storage_key)
    except StorageError as error:
        raise HTTPException(status_code=404, detail="Contenido documental no disponible") from error
    background_tasks.add_task(stream.close)
    visible_name = quote(document.nombre_original, safe="")
    return StreamingResponse(
        stream,
        media_type=document.tipo_mime,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{visible_name}"},
        background=background_tasks,
    )


@router.delete("/{order_id}/documentos/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_document(order_id: int, document_id: int, db: Session = Depends(get_db),
                        user: Usuario = Depends(get_current_user)) -> None:
    require_role(user, {"ADMINISTRADOR"})
    get_order(db, order_id)
    document = db.scalar(select(OrdenServicioDocumento).where(
        OrdenServicioDocumento.id == document_id,
        OrdenServicioDocumento.orden_servicio_id == order_id,
    ).with_for_update())
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if not document.activo:
        raise HTTPException(status_code=409, detail="El documento ya está inactivo")
    document.activo = False
    changes = audit_changes(document)
    changes["activo"] = {"antes": True, "despues": False}
    db.add(OrdenServicioAuditoria(
        orden_servicio_id=order_id,
        usuario_id=user.id,
        accion="DOCUMENTO_ELIMINADO",
        fecha_hora=datetime.now(LIMA),
        cambios=changes,
    ))
    db.commit()
