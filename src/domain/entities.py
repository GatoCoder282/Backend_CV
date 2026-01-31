from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
from .exceptions import InvalidUserError

class UserRole(str, Enum):
    ADMIN = "admin"
    GUEST = "guest"

@dataclass
class User:
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.GUEST
    
    id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

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

    def __post_init__(self):
        """
        Aquí normalizamos y validamos. 
        Al ejecutarse tras la creación, garantizamos que el objeto NUNCA
        existirá con datos sucios en memoria.
        """
        # 1. Normalización (Limpieza y Formato)
        # .strip() quita espacios adelante y atrás
        # .title() pone Mayúscula A Cada Palabra (soporta "Juan Carlos")
        if self.name:
            self.name = " ".join(self.name.split()).title()
        
        if self.last_name:
            self.last_name = " ".join(self.last_name.split()).title()

        if self.email:
             self.email = self.email.strip().lower() # Emails siempre en minúscula

        # 2. Validación (Reglas de Negocio)
        if not self.name or not self.last_name:
            raise InvalidUserError("El nombre y el apellido son obligatorios.")

    @property
    def full_name(self) -> str:
        """Propiedad computada para obtener el nombre completo cuando lo necesites."""
        return f"{self.name} {self.last_name}"

    def update_bio(self, new_bio: str):
        if len(new_bio) > 500:
            raise InvalidUserError("La biografía no puede exceder 500 caracteres.")
        self.bio_summary = new_bio