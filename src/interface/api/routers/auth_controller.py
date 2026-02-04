from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm

# Imports de Infraestructura
from src.infrastructure.data_base.main import get_session
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.security import Argon2PasswordHasher, JwtTokenManager

# Imports de Aplicación
from src.application.services.authentication import AuthService
from src.application.dtos.schemas import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse

# Imports de Interface (Dependencias)
from src.interface.api.authorization import get_current_user, get_current_admin

# Imports de Dominio
from src.domain.entities import User
from src.domain.exceptions import UserAlreadyExistsError

# Definimos el router (estándar: llamarlo 'router')
router = APIRouter(prefix="/auth", tags=["Auth"])

# --- FACTORY DE SERVICIOS (Dependency Injection) ---
def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    """
    Ensambla el servicio de autenticación con sus adaptadores reales.
    Si mañana cambias Argon2 por otro, solo cambias esta línea.
    """
    repo = SqlAlchemyUserRepository(session)
    hasher = Argon2PasswordHasher()
    token_manager = JwtTokenManager()
    return AuthService(repo, hasher, token_manager)

# --- ENDPOINTS ---

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegisterRequest, 
    service: AuthService = Depends(get_auth_service)
):
    """
    Registro de usuarios:
    - Por defecto crea ADMIN (pueden administrar su propio portfolio/CMS)
    - Si el email coincide con SUPERADMIN_EMAIL, crea SUPERADMIN automáticamente
    - Multi-tenant: cada usuario solo puede editar su propio contenido
    """
    try:
        new_user = service.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        return new_user
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

@router.post("/login", response_model=TokenResponse)
def login(
    # CAMBIO CLAVE: Ahora aceptamos el formulario estándar de Swagger/FastAPI
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthService = Depends(get_auth_service)
):
    """
    Login compatible con Swagger UI (OAuth2).
    Nota: Swagger enviará el email en el campo 'username'.
    """
    # Swagger envía los campos 'username' y 'password'.
    # Como tu sistema usa email, pasamos form_data.username como el email.
    token_data = service.login_user(form_data.username, form_data.password)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Credenciales incorrectas"
        )
    return token_data

# --- ZONA DE PRUEBAS DE ROLES ---

@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """Ruta protegida: Verifica que el Token sea válido."""
    return current_user

@router.get("/admin-only")
def admin_zone(
    current_user: User = Depends(get_current_admin)
):
    """Ruta protegida: Verifica que el usuario tenga rol ADMIN."""
    return {
        "message": f"Acceso concedido al panel de control.",
        "admin_user": current_user.username
    }