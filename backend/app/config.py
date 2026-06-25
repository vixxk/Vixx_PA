import json
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Populate os.environ with variables from .env
load_dotenv()

class Settings(BaseSettings):
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://vixx:password@localhost:5432/work_os"

    # JWT Authentication
    JWT_SECRET_KEY: str = "placeholder_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI Keys
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Google Sync
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # GitHub Sync
    GITHUB_ACCESS_TOKEN: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Meta WhatsApp Cloud API
    META_WHATSAPP_ACCESS_TOKEN: str = ""
    META_WHATSAPP_PHONE_NUMBER_ID: str = ""
    META_WHATSAPP_VERSION: str = "v20.0"
    USER_WHATSAPP_NUMBER: str = "+91XXXXXXXXXX"
    META_WHATSAPP_TEMPLATE_NAME: str = ""
    META_WHATSAPP_TEMPLATE_LANG: str = "en_US"

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
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
