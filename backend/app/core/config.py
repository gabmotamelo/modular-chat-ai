from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_PORT: int = 8080
    REDIS_URL: str = "redis://red-d2m47o7fte5s739da33g:6379"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "*"

settings = Settings()
