from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session

from src.infrastructure.data_base.main import get_session
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.security import JwtTokenManager
from src.domain.entities import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Instanciamos el manager de tokens (infraestructura)
# En un framework de inyección más complejo esto sería automático, 
# pero aquí lo hacemos explícito y simple.
token_manager = JwtTokenManager()

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Usamos nuestro adaptador JWT para decodificar
        payload = token_manager.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    repo = SqlAlchemyUserRepository(session)
    user = repo.get_by_email(email)
    
    if user is None:
        raise credentials_exception
        
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Guardian estricto para rutas de Admin (CMS)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user