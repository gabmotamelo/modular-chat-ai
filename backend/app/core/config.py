from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_PORT: int = 8080
    REDIS_URL: str = "redis://redis:6379/0"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "*"

settings = Settings()
