from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Definición de variables requeridas
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    environment: str = "dev"

    # Configuración para leer el archivo .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Singleton con caché: lee el disco solo una vez
@lru_cache
def get_settings():
    return Settings()

settings = get_settings()