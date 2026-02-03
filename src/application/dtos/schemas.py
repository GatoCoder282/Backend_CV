from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field

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