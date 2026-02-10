from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pydantic import Field, field_validator

class Settings(BaseSettings):
    # Definición de variables requeridas
    database_url: str = Field(..., min_length=10)
    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    environment: str = "dev"

    superadmin_email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")

    cloudinary_cloud_name: str = Field(...)
    cloudinary_api_key: str = Field(...)
    cloudinary_api_secret: str = Field(...)

    supabase_url: str = Field(...)
    supabase_api_key: str = Field(...)
    supabase_service_key: str = Field(...)
    supabase_bucket_name: str = Field(default="porty_pdfs")

    # Configuración para leer el archivo .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validar que el environment sea uno de los valores permitidos."""
        allowed = {"dev", "staging", "prod"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT debe ser uno de: {allowed}")
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key_length(cls, v: str) -> str:
        """En producción, exigir SECRET_KEY más larga."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres (usa secrets.token_hex(32))")
        # Validación adicional: en producción aviso si parece un default
        if "your-secret" in v.lower() or "change-in-production" in v.lower():
            raise ValueError("⚠️ Cambiar SECRET_KEY del archivo .env.example")
        return v

# Singleton con caché: lee el disco solo una vez
@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    
    # Logging en startup
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Settings cargados para ambiente: {settings.environment}")
    
    if settings.environment == "prod":
        logger.warning("🔐 Modo PRODUCCIÓN habilitado. Asegurar HTTPS, backups, y monitoreo.")
    
    return settings

settings = get_settings()