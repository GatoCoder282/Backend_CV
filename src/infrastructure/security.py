from datetime import datetime, timedelta
from typing import Dict, Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from src.domain.ports import PasswordHasher, TokenManager
from src.infrastructure.config import settings

# --- ADAPTADOR 1: Argon2 ---
class Argon2PasswordHasher(PasswordHasher):
    def __init__(self):
        # Configuramos explicitamente para usar argon2
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

# --- ADAPTADOR 2: JWT ---
class JwtTokenManager(TokenManager):
    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Dict:
        # Este método lanzará JWTError si el token es inválido o expiró
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])