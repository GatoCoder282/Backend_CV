from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

# Imports de Infraestructura
from src.infrastructure.data_base.main import get_session
from src.infrastructure.repositories.technology_repository import SqlAlchemyTechnologyRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository

# Imports de Aplicación
from src.application.services.technology_service import (
    TechnologyService,
    TechnologyNotFoundError,
    UnauthorizedAccessError
)
from src.application.dtos.schemas import (
    TechnologyCreateRequest,
    TechnologyUpdateRequest,
    TechnologyResponse
)

# Imports de Interface (Dependencias)
from src.interface.api.authorization import get_current_user, get_current_admin

# Imports de Dominio
from src.domain.entities import User
from src.domain.exceptions import InvalidUserError, DomainException

router = APIRouter(prefix="/technologies", tags=["Technology"])

# --- FACTORY DE SERVICIOS ---
def get_technology_service(session: Session = Depends(get_session)) -> TechnologyService:
    """Ensambla el servicio de tecnologías."""
    tech_repo = SqlAlchemyTechnologyRepository(session)
    profile_repo = SqlAlchemyProfileRepository(session)
    return TechnologyService(tech_repo, profile_repo)

# --- ENDPOINTS ---

@router.post("", response_model=TechnologyResponse, status_code=status.HTTP_201_CREATED)
def create_technology(
    tech_data: TechnologyCreateRequest,
    current_user: User = Depends(get_current_admin),
    service: TechnologyService = Depends(get_technology_service)
):
    """
    Crea una tecnología para el usuario autenticado.
    Multi-tenant seguro: se asocia al perfil del usuario.
    """
    try:
        new_tech = service.create_technology(
            user_id=current_user.id,
            name=tech_data.name,
            category=tech_data.category,
            icon_url=tech_data.icon_url
        )
        return new_tech
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

@router.get("/me", response_model=List[TechnologyResponse])
def get_my_technologies(
    current_user: User = Depends(get_current_user),
    service: TechnologyService = Depends(get_technology_service)
):
    """
    Obtiene todas las tecnologías del usuario autenticado.
    Multi-tenant seguro: solo ve sus propias tecnologías.
    """
    try:
        return service.get_all_my_technologies(current_user.id)
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{tech_id}", response_model=TechnologyResponse)
def get_technology(
    tech_id: int,
    current_user: User = Depends(get_current_user),
    service: TechnologyService = Depends(get_technology_service)
):
    """
    Obtiene una tecnología específica.
    Multi-tenant seguro: solo puede ver sus propias tecnologías.
    """
    try:
        return service.get_technology_by_id(current_user.id, tech_id)
    except TechnologyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.put("/{tech_id}", response_model=TechnologyResponse)
def update_technology(
    tech_id: int,
    tech_data: TechnologyUpdateRequest,
    current_user: User = Depends(get_current_admin),
    service: TechnologyService = Depends(get_technology_service)
):
    """
    Actualiza una tecnología del usuario autenticado.
    Multi-tenant seguro: solo puede modificar sus propias tecnologías.
    """
    try:
        updated_tech = service.update_technology(
            user_id=current_user.id,
            tech_id=tech_id,
            name=tech_data.name,
            category=tech_data.category,
            icon_url=tech_data.icon_url
        )
        return updated_tech
    except TechnologyNotFoundError as e:
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

@router.delete("/{tech_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_technology(
    tech_id: int,
    current_user: User = Depends(get_current_admin),
    service: TechnologyService = Depends(get_technology_service)
):
    """
    Elimina (soft delete) una tecnología del usuario autenticado.
    Multi-tenant seguro: solo puede eliminar sus propias tecnologías.
    """
    try:
        service.delete_technology(current_user.id, tech_id)
        return None
    except TechnologyNotFoundError as e:
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

@router.get("/public/{username}", response_model=List[TechnologyResponse])
def get_public_technologies(
    username: str,
    session: Session = Depends(get_session)
):
    """
    Endpoint público: Obtiene todas las tecnologías de un usuario por su username.
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
        
        # Obtener tecnologías
        tech_repo = SqlAlchemyTechnologyRepository(session)
        technologies = tech_repo.get_all_by_profile_id(profile.id)
        
        return technologies
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener tecnologías: {str(e)}"
        )
