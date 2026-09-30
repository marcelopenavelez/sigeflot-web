from datetime import date
from io import BytesIO

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.main import app
from app.models import OrdenServicio, OrdenServicioAuditoria, OrdenServicioDocumento
from app.services.storage import LocalStorage, S3Storage, StorageError, get_storage
from .conftest import token


PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"
JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-data"
PNG = b"\x89PNG\r\n\x1a\n" + b"png-data"


class TrackingLocalStorage(LocalStorage):
    def __init__(self, root):
        super().__init__(root)
        self.deleted: list[str] = []
        self.fail_save = False

    def save(self, storage_key, source, content_type):
        if self.fail_save:
            raise StorageError("simulated failure")
        super().save(storage_key, source, content_type)

    def delete(self, storage_key):
        self.deleted.append(storage_key)
        super().delete(storage_key)


@pytest.fixture
def storage(tmp_path):
    backend = TrackingLocalStorage(tmp_path / "documents")
    app.dependency_overrides[get_storage] = lambda: backend
    yield backend
    app.dependency_overrides.pop(get_storage, None)


def headers(client, role="ADMINISTRADOR"):
    email = f"{role.lower()}@example.com"
    return {"Authorization": f"Bearer {token(client, email)}"}


def seed_order(db, *, historical=False, number="DOC-001"):
    order = OrdenServicio(
        numero_orden=number,
        fecha=date.today(),
        descripcion="Orden para documentos",
        estado="HISTORICO" if historical else "ABIERTA",
        estado_archivo="PENDIENTE",
        es_historico=historical,
        fuente_origen="HISTORICO" if historical else "OPERATIVO",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def upload(client, order_id, *, role="ADMINISTRADOR", filename="orden.pdf", content=PDF,
           mime="application/pdf", category="ORDEN_SERVICIO"):
    return client.post(
        f"/api/v1/ordenes-servicio/{order_id}/documentos",
        headers=headers(client, role),
        data={"categoria": category},
        files={"file": (filename, content, mime)},
    )


def test_admin_uploads_pdf_and_audit(client, db_session, storage):
    order = seed_order(db_session)
    response = upload(client, order.id)
    assert response.status_code == 201
    body = response.json()
    assert body["tipo_mime"] == "application/pdf"
    db_session.rollback()
    document = db_session.get(OrdenServicioDocumento, body["id"])
    assert storage.exists(document.storage_key)
    audit = db_session.scalar(select(OrdenServicioAuditoria).where(OrdenServicioAuditoria.accion == "DOCUMENTO_ADJUNTADO"))
    assert audit.cambios["documento_id"]["despues"] == document.id
    assert "storage_key" not in audit.cambios


@pytest.mark.parametrize(
    ("filename", "content", "mime"),
    [("evidencia.jpg", JPEG, "image/jpeg"), ("evidencia.png", PNG, "image/png")],
)
def test_mechanic_uploads_valid_images(client, db_session, storage, filename, content, mime):
    order = seed_order(db_session)
    response = upload(client, order.id, role="MECANICO", filename=filename, content=content, mime=mime, category="FOTOGRAFIA")
    assert response.status_code == 201
    assert response.json()["tipo_mime"] == mime


@pytest.mark.parametrize("role", ["CONSULTA", "CHOFER"])
def test_unauthorized_roles_cannot_upload(client, db_session, storage, role):
    order = seed_order(db_session)
    assert upload(client, order.id, role=role).status_code == 403
    assert db_session.scalar(select(func.count()).select_from(OrdenServicioDocumento)) == 0


def test_historical_order_accepts_document(client, db_session, storage):
    order = seed_order(db_session, historical=True)
    assert upload(client, order.id).status_code == 201


@pytest.mark.parametrize(
    ("filename", "content", "mime", "expected"),
    [
        ("empty.pdf", b"", "application/pdf", 422),
        ("script.exe", b"MZ", "application/octet-stream", 422),
        ("script.exe.pdf", PDF, "application/pdf", 422),
        ("wrong.pdf", PDF, "text/plain", 422),
        ("fake.pdf", PNG, "application/pdf", 422),
    ],
)
def test_rejects_invalid_files(client, db_session, storage, filename, content, mime, expected):
    order = seed_order(db_session)
    assert upload(client, order.id, filename=filename, content=content, mime=mime).status_code == expected


def test_rejects_oversized_file(client, db_session, storage, monkeypatch):
    order = seed_order(db_session)
    from app.api import order_documents

    monkeypatch.setattr(order_documents.get_settings(), "storage_max_file_size_bytes", 8)
    response = upload(client, order.id, content=PDF)
    assert response.status_code == 413


def test_unsafe_name_never_reaches_storage_key(client, db_session, storage):
    order = seed_order(db_session)
    response = upload(client, order.id, filename="../../factura.pdf")
    assert response.status_code == 201
    db_session.rollback()
    document = db_session.get(OrdenServicioDocumento, response.json()["id"])
    assert document.nombre_original == "factura.pdf"
    assert "factura" not in document.storage_key
    assert ".." not in document.storage_key


def test_same_filename_uses_distinct_objects(client, db_session, storage):
    order = seed_order(db_session)
    first = upload(client, order.id).json()
    second = upload(client, order.id).json()
    db_session.rollback()
    one = db_session.get(OrdenServicioDocumento, first["id"])
    two = db_session.get(OrdenServicioDocumento, second["id"])
    assert one.storage_key != two.storage_key
    assert storage.exists(one.storage_key) and storage.exists(two.storage_key)


def test_list_and_download_authorization(client, db_session, storage):
    order = seed_order(db_session)
    document = upload(client, order.id).json()
    for role in ("ADMINISTRADOR", "MECANICO", "CONSULTA"):
        listed = client.get(f"/api/v1/ordenes-servicio/{order.id}/documentos", headers=headers(client, role))
        assert listed.status_code == 200 and [item["id"] for item in listed.json()] == [document["id"]]
    downloaded = client.get(
        f"/api/v1/ordenes-servicio/{order.id}/documentos/{document['id']}",
        headers=headers(client, "CONSULTA"),
    )
    assert downloaded.status_code == 200
    assert downloaded.content == PDF
    assert downloaded.headers["content-type"].startswith("application/pdf")
    assert client.get(
        f"/api/v1/ordenes-servicio/{order.id}/documentos/{document['id']}",
        headers=headers(client, "CHOFER"),
    ).status_code == 403


def test_document_cannot_be_downloaded_through_another_order(client, db_session, storage):
    one = seed_order(db_session, number="DOC-ONE")
    two = seed_order(db_session, number="DOC-TWO")
    document = upload(client, one.id).json()
    response = client.get(
        f"/api/v1/ordenes-servicio/{two.id}/documentos/{document['id']}",
        headers=headers(client),
    )
    assert response.status_code == 404


@pytest.mark.parametrize("role", ["MECANICO", "CONSULTA", "CHOFER"])
def test_only_admin_can_delete(client, db_session, storage, role):
    order = seed_order(db_session)
    document = upload(client, order.id).json()
    response = client.delete(
        f"/api/v1/ordenes-servicio/{order.id}/documentos/{document['id']}",
        headers=headers(client, role),
    )
    assert response.status_code == 403


def test_admin_logical_delete_hides_document_and_audits(client, db_session, storage):
    order = seed_order(db_session)
    document_data = upload(client, order.id).json()
    db_session.rollback()
    document = db_session.get(OrdenServicioDocumento, document_data["id"])
    storage_key = document.storage_key
    url = f"/api/v1/ordenes-servicio/{order.id}/documentos/{document.id}"
    assert client.delete(url, headers=headers(client)).status_code == 204
    db_session.rollback()
    assert db_session.get(OrdenServicioDocumento, document.id).activo is False
    assert storage.exists(storage_key)
    assert client.get(f"/api/v1/ordenes-servicio/{order.id}/documentos", headers=headers(client)).json() == []
    assert client.get(url, headers=headers(client)).status_code == 404
    assert client.delete(url, headers=headers(client)).status_code == 409
    audit = db_session.scalar(select(OrdenServicioAuditoria).where(OrdenServicioAuditoria.accion == "DOCUMENTO_ELIMINADO"))
    assert audit.cambios["activo"] == {"antes": True, "despues": False}


def test_storage_failure_creates_no_metadata(client, db_session, storage):
    order = seed_order(db_session)
    storage.fail_save = True
    assert upload(client, order.id).status_code == 503
    assert db_session.scalar(select(func.count()).select_from(OrdenServicioDocumento)) == 0


def test_database_failure_attempts_storage_compensation(client, db_session, storage, monkeypatch):
    order = seed_order(db_session)
    request_headers = headers(client)

    def fail_commit(self):
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    response = client.post(
        f"/api/v1/ordenes-servicio/{order.id}/documentos",
        headers=request_headers,
        data={"categoria": "ORDEN_SERVICIO"},
        files={"file": ("orden.pdf", PDF, "application/pdf")},
    )
    assert response.status_code == 500
    assert len(storage.deleted) == 1
    assert not storage.exists(storage.deleted[0])


def test_s3_storage_uses_private_object_operations(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.body = b""
            self.deleted = False

        def upload_fileobj(self, source, bucket, key, ExtraArgs):
            assert bucket == "private-bucket" and key == "ordenes/1/file.pdf"
            assert ExtraArgs == {"ContentType": "application/pdf"}
            self.body = source.read()

        def get_object(self, **kwargs):
            return {"Body": BytesIO(self.body)}

        def head_object(self, **kwargs):
            return {}

        def delete_object(self, **kwargs):
            self.deleted = True

    fake = FakeClient()
    monkeypatch.setattr("app.services.storage.boto3.client", lambda *args, **kwargs: fake)
    backend = S3Storage(bucket="private-bucket")
    backend.save("ordenes/1/file.pdf", BytesIO(PDF), "application/pdf")
    assert backend.exists("ordenes/1/file.pdf")
    assert backend.open("ordenes/1/file.pdf").read() == PDF
    backend.delete("ordenes/1/file.pdf")
    assert fake.deleted is True
