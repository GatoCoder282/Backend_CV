from sqlmodel import create_engine, Session, SQLModel
from typing import Generator
from src.infrastructure.config import settings # Importación absoluta

# Detectar si es SQLite para configuración específica
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

# Crear el motor usando la variable de entorno
engine = create_engine(
    settings.database_url, 
    echo=(settings.environment == "dev"), # Solo imprime SQL en desarrollo
    connect_args=connect_args
)

def create_db_and_tables():
    """Crea las tablas en la DB (útil para dev)."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency Injection para FastAPI."""
    with Session(engine) as session:
        yield session