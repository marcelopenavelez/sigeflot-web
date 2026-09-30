from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath
from typing import BinaryIO

import boto3

from app.core.config import Settings, get_settings


class StorageError(RuntimeError):
    """Raised when an object cannot be persisted or retrieved."""


class StorageBackend(ABC):
    @abstractmethod
    def save(self, storage_key: str, source: BinaryIO, content_type: str) -> None: ...

    @abstractmethod
    def open(self, storage_key: str) -> BinaryIO: ...

    @abstractmethod
    def exists(self, storage_key: str) -> bool: ...

    @abstractmethod
    def delete(self, storage_key: str) -> None: ...


def _safe_key(storage_key: str) -> PurePosixPath:
    key = PurePosixPath(storage_key)
    if key.is_absolute() or not key.parts or any(part in {"", ".", ".."} for part in key.parts):
        raise StorageError("Clave de almacenamiento inválida")
    return key


class LocalStorage(StorageBackend):
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _path(self, storage_key: str) -> Path:
        key = _safe_key(storage_key)
        path = self.root.joinpath(*key.parts).resolve()
        if path != self.root and self.root not in path.parents:
            raise StorageError("Clave de almacenamiento fuera de la raíz")
        return path

    def save(self, storage_key: str, source: BinaryIO, content_type: str) -> None:
        del content_type
        path = self._path(storage_key)
        if path.exists():
            raise StorageError("La clave de almacenamiento ya existe")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
        except (OSError, ValueError) as error:
            raise StorageError("No fue posible guardar el archivo") from error

    def open(self, storage_key: str) -> BinaryIO:
        try:
            return self._path(storage_key).open("rb")
        except OSError as error:
            raise StorageError("No fue posible abrir el archivo") from error

    def exists(self, storage_key: str) -> bool:
        return self._path(storage_key).is_file()

    def delete(self, storage_key: str) -> None:
        try:
            self._path(storage_key).unlink(missing_ok=True)
        except OSError as error:
            raise StorageError("No fue posible eliminar el archivo") from error


class S3Storage(StorageBackend):
    def __init__(self, *, bucket: str, endpoint_url: str | None = None, region: str | None = None,
                 access_key_id: str | None = None, secret_access_key: str | None = None):
        if not bucket:
            raise ValueError("STORAGE_BUCKET es obligatorio para S3")
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or None,
            region_name=region or None,
            aws_access_key_id=access_key_id or None,
            aws_secret_access_key=secret_access_key or None,
        )

    def save(self, storage_key: str, source: BinaryIO, content_type: str) -> None:
        key = str(_safe_key(storage_key))
        try:
            self.client.upload_fileobj(source, self.bucket, key, ExtraArgs={"ContentType": content_type})
        except Exception as error:
            raise StorageError("No fue posible guardar el archivo") from error

    def open(self, storage_key: str) -> BinaryIO:
        try:
            return self.client.get_object(Bucket=self.bucket, Key=str(_safe_key(storage_key)))["Body"]
        except Exception as error:
            raise StorageError("No fue posible abrir el archivo") from error

    def exists(self, storage_key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=str(_safe_key(storage_key)))
            return True
        except Exception:
            return False

    def delete(self, storage_key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=str(_safe_key(storage_key)))
        except Exception as error:
            raise StorageError("No fue posible eliminar el archivo") from error


def build_storage(settings: Settings) -> StorageBackend:
    if settings.storage_backend == "local":
        return LocalStorage(settings.storage_local_root)
    return S3Storage(
        bucket=settings.storage_bucket or "",
        endpoint_url=settings.storage_endpoint_url,
        region=settings.storage_region,
        access_key_id=settings.storage_access_key_id,
        secret_access_key=settings.storage_secret_access_key,
    )


def get_storage() -> StorageBackend:
    return build_storage(get_settings())
