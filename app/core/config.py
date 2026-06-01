import json
from functools import lru_cache
from typing import Annotated, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    # --- app metadata
    TITLE: str = "Base Backend API"
    DESCRIPTION: str = "Production-ready FastAPI backend with auth"
    VERSION: str = "1.0.0"

    # --- environment
    ENV: str = "dev"
    DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # --- database
    WRITER_DB_URL: str = (
        "postgresql+asyncpg://basebackend_user:basebackend_pwd@db:5432/postgres"
    )
    READER_DB_URL: Optional[str] = None
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # --- db SSL
    DB_SSL_MODE: str = "disable"  # disable | require | verify-ca | verify-full
    DB_SSL_ROOT_CERT_PATH: Optional[str] = None
    DB_SSL_CLIENT_CERT_PATH: Optional[str] = None
    DB_SSL_CLIENT_KEY_PATH: Optional[str] = None

    # --- JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "base-backend"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 900
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400

    # --- CORS
    ALLOW_ORIGINS: Annotated[List[str], NoDecode] = ["*"]
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: Annotated[List[str], NoDecode] = ["*"]
    ALLOW_HEADERS: Annotated[List[str], NoDecode] = ["*"]

    # --- external SSL
    EXTERNAL_SSL_ROOT_CA_PATH: Optional[str] = None
    CLIENT_CERT_PATH: Optional[str] = None
    CLIENT_KEY_PATH: Optional[str] = None
    SERVER_CERT_PATH: Optional[str] = None
    SERVER_KEY_PATH: Optional[str] = None
    ENABLE_MTLS: bool = False

    # --- logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # --- migrations
    RUN_MIGRATIONS_ON_STARTUP: bool = False

    # --- domain event delivery
    EVENT_DELIVERY_WORKER_ENABLED: bool = True
    EVENT_DELIVERY_POLL_INTERVAL_SECONDS: float = 1.0
    EVENT_DELIVERY_BATCH_SIZE: int = 100

    @field_validator("ALLOW_ORIGINS", "ALLOW_METHODS", "ALLOW_HEADERS", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @field_validator("READER_DB_URL", mode="before")
    @classmethod
    def _default_reader(cls, v):
        return None if v == "" else v

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() in {"prod", "production"}

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    def model_post_init(self, __context) -> None:
        if self.READER_DB_URL is None:
            self.READER_DB_URL = self.WRITER_DB_URL


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
