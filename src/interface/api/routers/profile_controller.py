from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

# Imports de Infraestructura
from src.infrastructure.data_base.main import get_session
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository

# Imports de Aplicación
from src.application.services.profile_service import (
    ProfileService, 
    ProfileAlreadyExistsError, 
    ProfileNotFoundError
)
from src.application.dtos.schemas import (
    ProfileCreateRequest, 
    ProfileUpdateRequest, 
    ProfileResponse
)

# Imports de Interface (Dependencias)
from src.interface.api.authorization import get_current_user, get_current_admin

# Imports de Dominio
from src.domain.entities import User
from src.domain.exceptions import InvalidUserError

router = APIRouter(prefix="/profile", tags=["Profile"])

# --- FACTORY DE SERVICIOS ---
def get_profile_service(session: Session = Depends(get_session)) -> ProfileService:
    """Ensambla el servicio de perfiles."""
    repo = SqlAlchemyProfileRepository(session)
    return ProfileService(repo)

# --- ENDPOINTS ---

@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_data: ProfileCreateRequest,
    current_user: User = Depends(get_current_admin),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Crea un perfil para el usuario autenticado.
    Solo puede crear un perfil, no más.
    """
    try:
        new_profile = service.create_profile(
            user_id=current_user.id,
            name=profile_data.name,
            last_name=profile_data.last_name,
            email=current_user.email,
            current_title=profile_data.current_title,
            bio_summary=profile_data.bio_summary,
            phone=profile_data.phone,
            location=profile_data.location,
            photo_url=profile_data.photo_url,
            profile=profile_data.profile,
            created_by=current_user.id
        )
        return new_profile
    except ProfileAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except InvalidUserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Obtiene el perfil del usuario autenticado.
    Multi-tenant seguro: Solo ve su propio perfil.
    """
    try:
        profile = service.get_my_profile(current_user.id)
        return profile
    except ProfileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_admin),
    service: ProfileService = Depends(get_profile_service)
):
    """
    Actualiza el perfil del usuario autenticado.
    Multi-tenant seguro: Solo modifica su propio perfil.
    """
    try:
        updated_profile = service.update_my_profile(
            user_id=current_user.id,
            name=profile_data.name,
            last_name=profile_data.last_name,
            email=current_user.email,
            current_title=profile_data.current_title,
            bio_summary=profile_data.bio_summary,
            phone=profile_data.phone,
            location=profile_data.location,
            photo_url=profile_data.photo_url,
            profile=profile_data.profile
        )
        return updated_profile
    except ProfileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidUserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# --- ENDPOINTS PÚBLICOS ---

@router.get("/public/{username}", response_model=ProfileResponse)
def get_public_profile(
    username: str,
    session: Session = Depends(get_session)
):
    """
    Endpoint público: Obtiene el perfil de un usuario por su username.
    No requiere autenticación.
    """
    try:
        # Buscar usuario por username
        user_repo = SqlAlchemyUserRepository(session)
        user = user_repo.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado."
            )
        
        # Buscar perfil del usuario
        profile_repo = SqlAlchemyProfileRepository(session)
        profile = profile_repo.get_by_user_id(user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil no encontrado."
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el perfil: {str(e)}"
        )
