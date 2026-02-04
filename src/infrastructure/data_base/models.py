from typing import Optional
from datetime import datetime, date
from sqlmodel import Field, SQLModel
from src.domain.entities import UserRole, ProjectCategory, TechnologyCategory # Importamos los Enums del dominio

# --- MODELO DE USUARIO ---
class UserModel(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default=UserRole.ADMIN.value) # Guardamos el string del Enum
    
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

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
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

# --- EXPERIENCIA LABORAL ---
class WorkExperienceModel(SQLModel, table=True):
    __tablename__ = "work_experience"

    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id")

    job_title: str
    company: str
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

# --- PROYECTOS ---
class ProjectModel(SQLModel, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id")

    title: str
    category: str = Field(default=ProjectCategory.FULLSTACK.value)  # Enum como string
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    live_url: Optional[str] = None
    repo_url: Optional[str] = None
    featured: bool = False
    
    # Relación opcional: proyecto desarrollado en una experiencia laboral
    work_experience_id: Optional[int] = Field(default=None, foreign_key="work_experience.id")
    
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

# --- TECNOLOGÍAS ---
class TechnologyModel(SQLModel, table=True):
    __tablename__ = "technologies"

    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id")
    name: str
    category: str  # Enum como string
    icon_url: Optional[str] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

# --- RELACIÓN PROYECTO-TECNOLOGÍA ---
class ProjectTechModel(SQLModel, table=True):
    __tablename__ = "project_tech"

    project_id: int = Field(foreign_key="projects.id", primary_key=True)
    tech_id: int = Field(foreign_key="technologies.id", primary_key=True)
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

# --- CLIENTES Y FEEDBACK ---
class ClientModel(SQLModel, table=True):
    __tablename__ = "clients"

    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id")

    name: str
    company: Optional[str] = None
    feedback: Optional[str] = None
    client_photo_url: Optional[str] = None
    project_link: Optional[str] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

# --- SOCIAL LINKS ---
class SocialModel(SQLModel, table=True):
    __tablename__ = "socials"

    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profiles.id")

    platform: str  # Ej: "GitHub", "LinkedIn", "Twitter"
    url: str
    icon_name: Optional[str] = None  # Para el icono a mostrar
    order: int = Field(default=0)  # Para ordenar los links
    
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

# --- PROJECT PREVIEWS (IMÁGENES DE PROYECTO) ---
class ProjectPreviewModel(SQLModel, table=True):
    __tablename__ = "project_previews"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")

    image_url: str  # URL de Cloudinary
    caption: Optional[str] = None  # Ej: "Vista del panel de control"
    order: int = Field(default=0)  # Para ordenar qué foto va primero en el carrusel
    
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True