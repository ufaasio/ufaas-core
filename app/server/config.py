"""FastAPI server configuration."""

import dataclasses
import logging
import logging.config
import os
from pathlib import Path

import dotenv
from singleton import Singleton

dotenv.load_dotenv()


@dataclasses.dataclass
class Settings(metaclass=Singleton):
    """Server config settings."""

    base_dir: Path = Path(__file__).resolve().parent.parent
    root_url: str = os.getenv("DOMAIN", default="http://localhost:8000")
    project_name: str = os.getenv("PROJECT_NAME", default="UFaaS")

    page_max_limit: int = 100
    coverage_dir: Path = base_dir / "htmlcov"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", default="sqlite+aiosqlite:///logs/app.db"
    )
    # DATABASE_URL: str = os.getenv(
    #     "DATABASE_URL", default="sqlite:///:memory:"
    # )
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL_SYNC", default="sqlite:///./test.db"
    )
    mongo_uri: str = os.getenv("MONGO_URI", default="mongodb://localhost:27017")

    JWT_CONFIG: str = os.getenv(
        "USSO_JWT_CONFIG",
        default='{"jwk_url": "https://usso.io/website/jwks.json","type": "RS256","header": {"type": "Cookie", "name": "usso_access_token"} }',
    )
    USSO_API_KEY: str = os.getenv("USSO_API_KEY")
    USSO_URL: str = os.getenv("USSO_URL", default="https://sso.usso.io")
    USSO_USER_ID: str = os.getenv("USSO_USER_ID")
    business_domains_url = (
        os.getenv(
            "UFAAS_BUSINESS_DOMAINS_URL",
            "https://business.ufaas.io/api/v1/apps/business",
        )
        + "/businesses/"
    )

    testing: bool = os.getenv("TESTING", default=False)

    log_config = {
        "version": 1,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "standard",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "filename": base_dir / "logs" / f"{project_name}.log",
                "formatter": "standard",
            },
        },
        "formatters": {
            "standard": {
                "format": "[{levelname} : {filename}:{lineno} : {asctime} -> {funcName:10}] {message}",
                # "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                "style": "{",
            }
        },
        "loggers": {
            "": {
                "handlers": [
                    "console",
                    "file",
                ],
                "level": "INFO",
                "propagate": True,
            }
        },
    }

    @classmethod
    def config_logger(cls):
        if not (cls.base_dir / "logs").exists():
            (cls.base_dir / "logs").mkdir()

        logging.config.dictConfig(cls.log_config)
