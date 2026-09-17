import json
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend/.env is always loaded regardless of working directory
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

class Settings(BaseSettings):
    PORT: int = 5000
    HOST: str = "0.0.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://vixx:password@localhost:5432/work_os"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        if v and v.startswith("postgresql"):
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(v)
            query = parse_qs(parsed.query)
            query.pop("sslmode", None)
            query.pop("channel_binding", None)
            query["ssl"] = ["require"]
            new_query = urlencode(query, doseq=True)
            scheme = "postgresql+asyncpg"
            parsed = parsed._replace(scheme=scheme, query=new_query)
            return urlunparse(parsed)
        return v

    # JWT Authentication
    JWT_SECRET_KEY: str = "placeholder_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI Keys
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # Google Sync
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # GitHub Sync
    GITHUB_ACCESS_TOKEN: str = ""
    GITHUB_CLIENT_ID: str = ""

    # Twilio SMS API
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    USER_SMS_NUMBER: str = "+917253648994"

    # Green API (WhatsApp)
    GREEN_API_INSTANCE_ID: str = ""
    GREEN_API_API_TOKEN_INSTANCE: str = ""
    GREEN_API_HOST: str = "https://api.green-api.com"
    DEFAULT_WHATSAPP_NUMBER: str = ""


    # CORS Origins
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [i.strip() for i in v.replace("[", "").replace("]", "").replace("'", "").replace('"', '').split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=str(_env_path),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
