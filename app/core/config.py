from functools import lru_cache
from os import getenv
from secrets import token_urlsafe

from pydantic import BaseModel, Field

PROCESS_SECRET = token_urlsafe(48)


class Settings(BaseModel):
    database_url: str = Field(
        default_factory=lambda: getenv(
            "DATABASE_URL",
            "sqlite:////tmp/labflow.db" if getenv("VERCEL") else "sqlite:///./labflow.db",
        )
    )
    secret_key: str = Field(default_factory=lambda: getenv("SECRET_KEY", PROCESS_SECRET))
    access_token_expire_minutes: int = Field(
        default_factory=lambda: int(getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
