from datetime import datetime

from pydantic import BaseModel


class OrderDocumentRead(BaseModel):
    id: int
    nombre_original: str
    tipo_mime: str
    extension: str
    tamano_bytes: int
    categoria: str
    fecha_subida: datetime
    usuario: str
    activo: bool
