"""FastAPI server configuration."""

import dataclasses
import os
from pathlib import Path

import dotenv
from ufaas_fastapi_business.core.config import Settings as BaseSettings

dotenv.load_dotenv()


@dataclasses.dataclass
class Settings(BaseSettings):
    """Server config settings."""

    base_dir: Path = Path(__file__).resolve().parent.parent
    coverage_dir: Path = base_dir / "htmlcov"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", default="sqlite+aiosqlite:///logs/app.db"
    )
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL_SYNC", default="sqlite:///./test.db"
    )

    USSO_API_KEY: str = os.getenv("USSO_ADMIN_API_KEY")
    USSO_URL: str = os.getenv("USSO_URL", default="https://sso.usso.io")
    USSO_USER_ID: str = os.getenv("USSO_USER_ID")
