from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

# Imports de Infraestructura
from src.infrastructure.data_base.main import get_session
from src.infrastructure.repositories.work_experience_repository import WorkExperienceRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository

# Imports de Aplicación
from src.application.services.work_experience_service import (
    WorkExperienceService,
    WorkExperienceNotFoundError,
    UnauthorizedAccessError
)
from src.application.dtos.schemas import (
    WorkExperienceCreateRequest,
    WorkExperienceUpdateRequest,
    WorkExperienceResponse
)

# Imports de Interface (Dependencias)
from src.interface.api.authorization import get_current_user, get_current_admin

# Imports de Dominio
from src.domain.entities import User
from src.domain.exceptions import InvalidUserError, DomainException

router = APIRouter(prefix="/work-experience", tags=["Work Experience"])

# --- FACTORY DE SERVICIOS ---
def get_work_experience_service(session: Session = Depends(get_session)) -> WorkExperienceService:
    """Ensambla el servicio de experiencias laborales."""
    work_exp_repo = WorkExperienceRepository(session)
    profile_repo = SqlAlchemyProfileRepository(session)
    return WorkExperienceService(work_exp_repo, profile_repo)

# --- ENDPOINTS ---

@router.post("", response_model=WorkExperienceResponse, status_code=status.HTTP_201_CREATED)
def create_work_experience(
    work_exp_data: WorkExperienceCreateRequest,
    current_user: User = Depends(get_current_admin),
    service: WorkExperienceService = Depends(get_work_experience_service)
):
    """
    Crea una experiencia laboral para el usuario autenticado.
    Multi-tenant seguro: Se asocia automáticamente al perfil del usuario.
    """
    try:
        new_work_exp = service.create_work_experience(
            user_id=current_user.id,
            job_title=work_exp_data.job_title,
            company=work_exp_data.company,
            location=work_exp_data.location,
            start_date=work_exp_data.start_date,
            end_date=work_exp_data.end_date,
            description=work_exp_data.description
        )
        return new_work_exp
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

@router.get("/me", response_model=List[WorkExperienceResponse])
def get_my_work_experiences(
    current_user: User = Depends(get_current_user),
    service: WorkExperienceService = Depends(get_work_experience_service)
):
    """
    Obtiene todas las experiencias laborales del usuario autenticado.
    Multi-tenant seguro: Solo ve sus propias experiencias.
    """
    try:
        work_experiences = service.get_all_my_work_experiences(current_user.id)
        return work_experiences
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{work_experience_id}", response_model=WorkExperienceResponse)
def get_work_experience(
    work_experience_id: int,
    current_user: User = Depends(get_current_user),
    service: WorkExperienceService = Depends(get_work_experience_service)
):
    """
    Obtiene una experiencia laboral específica.
    Multi-tenant seguro: Solo puede ver sus propias experiencias.
    """
    try:
        work_experience = service.get_work_experience_by_id(current_user.id, work_experience_id)
        return work_experience
    except WorkExperienceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.put("/{work_experience_id}", response_model=WorkExperienceResponse)
def update_work_experience(
    work_experience_id: int,
    work_exp_data: WorkExperienceUpdateRequest,
    current_user: User = Depends(get_current_admin),
    service: WorkExperienceService = Depends(get_work_experience_service)
):
    """
    Actualiza una experiencia laboral del usuario autenticado.
    Multi-tenant seguro: Solo puede modificar sus propias experiencias.
    """
    try:
        updated_work_exp = service.update_work_experience(
            user_id=current_user.id,
            work_experience_id=work_experience_id,
            job_title=work_exp_data.job_title,
            company=work_exp_data.company,
            location=work_exp_data.location,
            start_date=work_exp_data.start_date,
            end_date=work_exp_data.end_date,
            description=work_exp_data.description
        )
        return updated_work_exp
    except WorkExperienceNotFoundError as e:
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

@router.delete("/{work_experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_experience(
    work_experience_id: int,
    current_user: User = Depends(get_current_admin),
    service: WorkExperienceService = Depends(get_work_experience_service)
):
    """
    Elimina (soft delete) una experiencia laboral del usuario autenticado.
    Multi-tenant seguro: Solo puede eliminar sus propias experiencias.
    """
    try:
        service.delete_work_experience(current_user.id, work_experience_id)
        return None
    except WorkExperienceNotFoundError as e:
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

@router.get("/public/{username}", response_model=List[WorkExperienceResponse])
def get_public_work_experiences(
    username: str,
    session: Session = Depends(get_session)
):
    """
    Endpoint público: Obtiene todas las experiencias laborales de un usuario por su username.
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
        
        # Obtener experiencias laborales
        work_exp_repo = WorkExperienceRepository(session)
        work_experiences = work_exp_repo.get_all_by_profile_id(profile.id)
        
        return work_experiences
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener experiencias laborales: {str(e)}"
        )
