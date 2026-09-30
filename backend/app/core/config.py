from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    # Railway and local environments must provide their own connection and secret.
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    storage_backend: str = "local"
    storage_local_root: str = ".data/documentos"
    storage_bucket: str | None = None
    storage_endpoint_url: str | None = None
    storage_region: str | None = None
    storage_access_key_id: str | None = None
    storage_secret_access_key: str | None = None
    storage_prefix: str = "ordenes"
    storage_max_file_size_bytes: int = 10 * 1024 * 1024
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_storage(self) -> "Settings":
        self.storage_backend = self.storage_backend.strip().lower()
        if self.storage_backend not in {"local", "s3"}:
            raise ValueError("STORAGE_BACKEND debe ser local o s3")
        if self.app_env.strip().lower() == "production" and self.storage_backend == "local":
            raise ValueError("STORAGE_BACKEND=local no está permitido en producción")
        if self.storage_max_file_size_bytes <= 0:
            raise ValueError("STORAGE_MAX_FILE_SIZE_BYTES debe ser mayor que cero")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
