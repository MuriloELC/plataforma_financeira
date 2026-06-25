from dataclasses import dataclass
from functools import lru_cache
import os


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    app_env: str
    cors_allow_origins: tuple[str, ...]
    database_url: str
    file_storage_path: str
    max_upload_size_bytes: int

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            user = _env("POSTGRES_USER", "finance_user")
            password = _env("POSTGRES_PASSWORD", "change_me")
            host = _env("POSTGRES_HOST", "localhost")
            port = _env("POSTGRES_PORT", "5432")
            database = _env("POSTGRES_DB", "finance_decision")
            database_url = (
                f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
            )

        return cls(
            app_env=_env("APP_ENV", "local"),
            cors_allow_origins=tuple(
                origin.strip()
                for origin in _env(
                    "CORS_ALLOW_ORIGINS",
                    "http://localhost:3000,http://127.0.0.1:3000",
                ).split(",")
                if origin.strip()
            ),
            database_url=database_url,
            file_storage_path=_env("FILE_STORAGE_PATH", "./storage"),
            max_upload_size_bytes=int(_env("MAX_UPLOAD_SIZE_BYTES", "20971520")),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
