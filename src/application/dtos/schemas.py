from typing import Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr, Field
from src.domain.entities import TechnologyCategory, ProjectCategory

# DTO para recibir datos (Input)
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr # Valida formato de email automáticamente
    password: str = Field(..., min_length=6)

# DTO para responder al cliente (Output)
# ¡IMPORTANTE! Nunca devolvemos el password_hash
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    
    class Config:
        from_attributes = True # Permite leer desde la entidad User

class UserLoginRequest(BaseModel):
    """Schema específico para login: Solo pide lo necesario."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """
    DTO estándar para respuestas de OAuth2.
    Devuelve el token y el tipo (generalmente 'bearer').
    """
    access_token: str
    token_type: str = "bearer" # Valor por defecto estándar

# --- PROFILE DTOs ---

# INPUT: Lo que envías para crear/editar
class ProfileCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    current_title: Optional[str] = None
    bio_summary: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = "Cochabamba, Bolivia"
    phone: Optional[str] = None
    photo_url: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    last_name: Optional[str] = Field(None, min_length=2)
    current_title: Optional[str] = None
    bio_summary: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None

# OUTPUT: Lo que devuelve la API
class ProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    last_name: str
    email: str
    current_title: Optional[str]
    bio_summary: Optional[str]
    location: Optional[str]
    phone: Optional[str]
    photo_url: Optional[str]
    
    class Config:
        from_attributes = True

# --- WORK EXPERIENCE DTOs ---

# INPUT: Lo que envías para crear
class WorkExperienceCreateRequest(BaseModel):
    job_title: str = Field(..., min_length=2)
    company: str = Field(..., min_length=2)
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None

# INPUT: Lo que envías para actualizar
class WorkExperienceUpdateRequest(BaseModel):
    job_title: Optional[str] = Field(None, min_length=2)
    company: Optional[str] = Field(None, min_length=2)
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

# OUTPUT: Lo que devuelve la API
class WorkExperienceResponse(BaseModel):
    id: int
    profile_id: int
    job_title: str
    company: str
    location: Optional[str]
    start_date: date
    end_date: Optional[date]
    description: Optional[str]
    
    class Config:
        from_attributes = True

# --- TECHNOLOGY DTOs ---

class TechnologyCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    category: TechnologyCategory
    icon_url: Optional[str] = None

class TechnologyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    category: Optional[TechnologyCategory] = None
    icon_url: Optional[str] = None

class TechnologyResponse(BaseModel):
    id: int
    profile_id: int
    name: str
    category: TechnologyCategory
    icon_url: Optional[str]

    class Config:
        from_attributes = True

# --- PROJECT DTOs ---

class ProjectPreviewCreateRequest(BaseModel):
    image_url: str
    caption: Optional[str] = None
    order: int = 0

class ProjectPreviewResponse(BaseModel):
    id: int
    project_id: int
    image_url: str
    caption: Optional[str]
    order: int

    class Config:
        from_attributes = True

class ProjectCreateRequest(BaseModel):
    title: str = Field(..., min_length=2)
    category: ProjectCategory
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    live_url: Optional[str] = None
    repo_url: Optional[str] = None
    featured: bool = False
    work_experience_id: Optional[int] = None
    technology_ids: List[int] = []
    previews: List[ProjectPreviewCreateRequest] = []

class ProjectUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2)
    category: Optional[ProjectCategory] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    live_url: Optional[str] = None
    repo_url: Optional[str] = None
    featured: Optional[bool] = None
    work_experience_id: Optional[int] = None
    technology_ids: Optional[List[int]] = None
    previews: Optional[List[ProjectPreviewCreateRequest]] = None

class ProjectResponse(BaseModel):
    id: int
    profile_id: int
    title: str
    category: ProjectCategory
    description: Optional[str]
    thumbnail_url: Optional[str]
    live_url: Optional[str]
    repo_url: Optional[str]
    featured: bool
    work_experience_id: Optional[int]
    technology_ids: List[int] = []
    previews: List[ProjectPreviewResponse] = []

    class Config:
        from_attributes = True

# --- CLIENT DTOs ---

class ClientCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    company: Optional[str] = None
    feedback: Optional[str] = None
    client_photo_url: Optional[str] = None
    project_link: Optional[str] = None

class ClientUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    company: Optional[str] = None
    feedback: Optional[str] = None
    client_photo_url: Optional[str] = None
    project_link: Optional[str] = None

class ClientResponse(BaseModel):
    id: int
    profile_id: int
    name: str
    company: Optional[str]
    feedback: Optional[str]
    client_photo_url: Optional[str]
    project_link: Optional[str]

    class Config:
        from_attributes = True

# --- SOCIAL DTOs ---

class SocialCreateRequest(BaseModel):
    platform: str = Field(..., min_length=2)
    url: str
    icon_name: Optional[str] = None
    order: int = 0

class SocialUpdateRequest(BaseModel):
    platform: Optional[str] = Field(None, min_length=2)
    url: Optional[str] = None
    icon_name: Optional[str] = None
    order: Optional[int] = None

class SocialResponse(BaseModel):
    id: int
    profile_id: int
    platform: str
    url: str
    icon_name: Optional[str]
    order: int

    class Config:
        from_attributes = True