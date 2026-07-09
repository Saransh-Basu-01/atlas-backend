from pydantic import SecretStr
from pydantic_settings import BaseSettings,SettingsConfigDict
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent  # app/core
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
    )

    DATABASE_URL: str
    SECRET_KEY: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    reset_token_expire_min: int = 60

settings = Settings()
