from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

# Imports de Infraestructura
from src.infrastructure.data_base.main import get_session
from src.infrastructure.repositories.social_repository import SqlAlchemySocialRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository

# Imports de Aplicación
from src.application.services.social_service import (
    SocialService,
    SocialNotFoundError,
    UnauthorizedAccessError
)
from src.application.dtos.schemas import (
    SocialCreateRequest,
    SocialUpdateRequest,
    SocialResponse
)

# Imports de Interface (Dependencias)
from src.interface.api.authorization import get_current_user, get_current_admin

# Imports de Dominio
from src.domain.entities import User
from src.domain.exceptions import InvalidUserError, DomainException

router = APIRouter(prefix="/social", tags=["Social"])

# --- FACTORY DE SERVICIOS ---
def get_social_service(session: Session = Depends(get_session)) -> SocialService:
    """Ensambla el servicio de social links."""
    social_repo = SqlAlchemySocialRepository(session)
    profile_repo = SqlAlchemyProfileRepository(session)
    return SocialService(social_repo, profile_repo)

# --- ENDPOINTS ---

@router.post("", response_model=SocialResponse, status_code=status.HTTP_201_CREATED)
def create_social(
    social_data: SocialCreateRequest,
    current_user: User = Depends(get_current_admin),
    service: SocialService = Depends(get_social_service)
):
    """
    Crea un social link para el usuario autenticado.
    Solo ADMIN puede crear.
    """
    try:
        new_social = service.create_social(
            user_id=current_user.id,
            platform=social_data.platform,
            url=social_data.url,
            icon_name=social_data.icon_name,
            order=social_data.order
        )
        return new_social
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidUserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=List[SocialResponse])
def get_my_socials(
    current_user: User = Depends(get_current_user),
    service: SocialService = Depends(get_social_service)
):
    """
    Obtiene todos los social links del usuario autenticado.
    """
    try:
        return service.get_all_my_socials(current_user.id)
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{social_id}", response_model=SocialResponse)
def get_social(
    social_id: int,
    current_user: User = Depends(get_current_user),
    service: SocialService = Depends(get_social_service)
):
    """
    Obtiene un social link específico.
    """
    try:
        return service.get_social_by_id(current_user.id, social_id)
    except SocialNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.put("/{social_id}", response_model=SocialResponse)
def update_social(
    social_id: int,
    social_data: SocialUpdateRequest,
    current_user: User = Depends(get_current_admin),
    service: SocialService = Depends(get_social_service)
):
    """
    Actualiza un social link del usuario autenticado.
    Solo ADMIN puede editar.
    """
    try:
        updated = service.update_social(
            user_id=current_user.id,
            social_id=social_id,
            platform=social_data.platform,
            url=social_data.url,
            icon_name=social_data.icon_name,
            order=social_data.order
        )
        return updated
    except SocialNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except InvalidUserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{social_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social(
    social_id: int,
    current_user: User = Depends(get_current_admin),
    service: SocialService = Depends(get_social_service)
):
    """
    Elimina (soft delete) un social link.
    Solo ADMIN puede eliminar.
    """
    try:
        service.delete_social(current_user.id, social_id)
        return None
    except SocialNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

# --- ENDPOINTS PÚBLICOS ---

@router.get("/public/{username}", response_model=List[SocialResponse])
def get_public_socials(
    username: str,
    session: Session = Depends(get_session)
):
    """
    Endpoint público: Obtiene todos los links sociales de un usuario por su username.
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
        
        # Obtener links sociales
        social_repo = SqlAlchemySocialRepository(session)
        socials = social_repo.get_all_by_profile_id(profile.id)
        
        return socials
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener links sociales: {str(e)}"
        )
