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