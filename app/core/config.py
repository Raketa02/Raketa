import json
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, validator


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
    ALLOW_ORIGINS: List[str] = ["*"]
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: List[str] = ["*"]
    ALLOW_HEADERS: List[str] = ["*"]

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

    @validator("ALLOW_ORIGINS", "ALLOW_METHODS", "ALLOW_HEADERS", pre=True)
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @validator("READER_DB_URL", always=True)
    def _default_reader(cls, v, values):
        return v or values.get("WRITER_DB_URL")

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() in {"prod", "production"}

    class Config:
        case_sensitive = True
        env_file = ".env"

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name in {"ALLOW_ORIGINS", "ALLOW_METHODS", "ALLOW_HEADERS"}:
                try:
                    return json.loads(raw_val)
                except json.JSONDecodeError:
                    return [s.strip() for s in raw_val.split(",") if s.strip()]
            return BaseSettings.Config.parse_env_var(field_name, raw_val)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
