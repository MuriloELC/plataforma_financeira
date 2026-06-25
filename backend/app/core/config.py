from dataclasses import dataclass
from functools import lru_cache
import os


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    file_storage_path: str

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
            database_url=database_url,
            file_storage_path=_env("FILE_STORAGE_PATH", "./storage"),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
