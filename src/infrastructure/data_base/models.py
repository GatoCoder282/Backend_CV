from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from src.domain.entities import UserRole # Reusamos el Enum del dominio

# --- MODELO DE USUARIO ---
class UserModel(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default=UserRole.GUEST.value) # Guardamos el string del Enum
    
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

# --- MODELO DE PERFIL ---
class ProfileModel(SQLModel, table=True):
    __tablename__ = "profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relación 1:1 con User (Foreign Key)
    user_id: int = Field(foreign_key="users.id", unique=True)
    
    # Datos Personales (Separados para normalización)
    name: str
    last_name: str
    
    # Datos de Contacto y Info
    email: str # Redundante con User, pero útil para consultas rápidas de perfil
    current_title: Optional[str] = None
    bio_summary: Optional[str] = Field(default=None, max_length=1000) # SQL VARCHAR(1000)
    phone: Optional[str] = None
    location: Optional[str] = "Cochabamba, Bolivia"
    photo_url: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.now)