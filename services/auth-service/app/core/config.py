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
    REFRESH_TOKEN_EXPIRE_DAYS:int=30
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    REFRESH_COOKIE_MAX_AGE_SECONDS: int = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES:int=15
    resend_api_key: str
    email_from: str
    frontend_url: str
    REDIS_URL:str
    REDIS_HOST:str
    REDIS_PORT:int
    REDIS_DB:int

    @property
    def redis_url(self):
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

settings = Settings()
