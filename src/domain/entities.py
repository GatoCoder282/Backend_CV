from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
from enum import Enum
from .exceptions import InvalidUserError

class UserRole(str, Enum):
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

class ProjectCategory(str, Enum):
    FULLSTACK = "fullstack"
    BACKEND = "backend"
    FRONTEND = "frontend"

class TechnologyCategory(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASES = "databases"
    APIS = "apis"
    DEV_TOOLS = "dev_tools"
    CLOUD = "cloud"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    SECURITY = "security"

@dataclass
class User:
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.ADMIN
    
    id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

    def __post_init__(self):
        """Validación de Dominio: Reglas que SIEMPRE deben cumplirse."""
        if not "@" in self.email:
            raise InvalidUserError("El email debe tener un formato válido.")
        if len(self.username) < 3:
            raise InvalidUserError("El username debe tener al menos 3 caracteres.")
        
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def update_last_login(self):
        self.last_login = datetime.now()

@dataclass
class Profile:
    user_id: int
    name: str
    last_name: str
    email: str
    
    # Campos opcionales / Nullables
    current_title: Optional[str] = None
    bio_summary: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = "Cochabamba, Bolivia"
    photo_url: Optional[str] = None
    
    # Auditoría
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

    def __post_init__(self):
        """
        Aquí normalizamos y validamos. 
        Al ejecutarse tras la creación, garantizamos que el objeto NUNCA
        existirá con datos sucios en memoria.
        """
        # 1. Normalización (Limpieza y Formato)
        # .strip() quita espacios adelante y atrás
        # .title() pone Mayúscula A Cada Palabra (soporta "Juan Carlos")
        if self.name is not None:
            self.name = " ".join(str(self.name).split()).title()
        
        if self.last_name is not None:
            self.last_name = " ".join(str(self.last_name).split()).title()

        if self.email is not None:
             self.email = str(self.email).strip().lower() # Emails siempre en minúscula

        # 2. Validación (Reglas de Negocio)
        if self.name is None or self.name == "" or self.last_name is None or self.last_name == "":
            raise InvalidUserError("El nombre y el apellido son obligatorios.")

    @property
    def full_name(self) -> str:
        """Propiedad computada para obtener el nombre completo cuando lo necesites."""
        return f"{self.name} {self.last_name}"

    def update_bio(self, new_bio: str):
        if len(new_bio) > 500:
            raise InvalidUserError("La biografía no puede exceder 500 caracteres.")
        self.bio_summary = new_bio

@dataclass
class WorkExperience:
    profile_id: int
    job_title: str
    company: str
    location: Optional[str] = None
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    description: Optional[str] = None

    id: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

    def __post_init__(self):
        if not self.job_title or not self.company:
            raise InvalidUserError("El cargo y la empresa son obligatorios.")
        if self.end_date and self.end_date < self.start_date:
            raise InvalidUserError("La fecha de fin no puede ser anterior a la de inicio.")

@dataclass
class Project:
    profile_id: int
    title: str
    category: ProjectCategory
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    live_url: Optional[str] = None
    repo_url: Optional[str] = None
    featured: bool = False
    
    work_experience_id: Optional[int] = None

    id: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

    def __post_init__(self):
        if not self.title:
            raise InvalidUserError("El título del proyecto es obligatorio.")

@dataclass
class Technology:
    profile_id: int
    name: str
    category: TechnologyCategory
    icon_url: Optional[str] = None

    id: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

    def __post_init__(self):
        if not self.name:
            raise InvalidUserError("El nombre de la tecnología es obligatorio.")

@dataclass
class ProjectTech:
    project_id: int
    tech_id: int
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

@dataclass
class Client:
    profile_id: int
    name: str
    company: Optional[str] = None
    feedback: Optional[str] = None
    client_photo_url: Optional[str] = None
    project_link: Optional[str] = None

    id: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

    def __post_init__(self):
        if not self.name:
            raise InvalidUserError("El nombre del cliente es obligatorio.")

@dataclass
class Social:
    profile_id: int
    platform: str  # Ej: "GitHub", "LinkedIn", "Twitter"
    url: str
    icon_name: Optional[str] = None  # Para el icono a mostrar
    order: int = 0  # Para ordenar los links

    id: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

    def __post_init__(self):
        if not self.platform or not self.url:
            raise InvalidUserError("La plataforma y la URL son obligatorios.")

@dataclass
class ProjectPreview:
    project_id: int
    image_url: str
    caption: Optional[str] = None
    order: int = 0  # Para ordenar las imágenes en el carrusel

    id: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: bool = True

    def __post_init__(self):
        if not self.image_url:
            raise InvalidUserError("La URL de la imagen es obligatoria.")