from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # IMPORTANT: keep these OUTSIDE app/ folder if you want to avoid uvicorn --reload reload storms
    OUTPUT_DIR: str = "./output"
    CLONE_DIR: str = "./clones"

    ANALYSIS_TTL_SECONDS: int = 60 * 60 * 24  # 24h
    CACHE_TTL_SECONDS: int = 60 * 60 * 24     # 24h


settings = Settings()