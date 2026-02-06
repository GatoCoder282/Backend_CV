from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

# Imports de Infraestructura
from src.infrastructure.data_base.main import get_session
from src.infrastructure.repositories.project_repository import (
    SqlAlchemyProjectRepository,
    SqlAlchemyProjectTechRepository,
    SqlAlchemyProjectPreviewRepository
)
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.work_experience_repository import WorkExperienceRepository
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository

# Imports de Aplicación
from src.application.services.project_service import (
    ProjectService,
    ProjectNotFoundError,
    UnauthorizedAccessError
)
from src.application.dtos.schemas import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectPreviewResponse
)

# Imports de Interface (Dependencias)
from src.interface.api.authorization import get_current_user, get_current_admin

# Imports de Dominio
from src.domain.entities import User
from src.domain.exceptions import InvalidUserError, DomainException

router = APIRouter(prefix="/projects", tags=["Projects"])

# --- FACTORY DE SERVICIOS ---
def get_project_service(session: Session = Depends(get_session)) -> ProjectService:
    """Ensambla el servicio de proyectos."""
    project_repo = SqlAlchemyProjectRepository(session)
    project_tech_repo = SqlAlchemyProjectTechRepository(session)
    project_preview_repo = SqlAlchemyProjectPreviewRepository(session)
    profile_repo = SqlAlchemyProfileRepository(session)
    work_exp_repo = WorkExperienceRepository(session)
    return ProjectService(
        project_repo,
        project_tech_repo,
        project_preview_repo,
        profile_repo,
        work_exp_repo
    )

# --- HELPERS ---
def build_project_response(
    project,
    project_tech_repo: SqlAlchemyProjectTechRepository,
    project_preview_repo: SqlAlchemyProjectPreviewRepository
) -> ProjectResponse:
    tech_ids = project_tech_repo.get_technologies_by_project_id(project.id)
    previews = project_preview_repo.get_by_project_id(project.id)
    preview_responses = [
        ProjectPreviewResponse(
            id=p.id,
            project_id=p.project_id,
            image_url=p.image_url,
            caption=p.caption,
            order=p.order
        ) for p in previews
    ]
    return ProjectResponse(
        id=project.id,
        profile_id=project.profile_id,
        title=project.title,
        category=project.category,
        description=project.description,
        thumbnail_url=project.thumbnail_url,
        live_url=project.live_url,
        repo_url=project.repo_url,
        featured=project.featured,
        work_experience_id=project.work_experience_id,
        technology_ids=tech_ids,
        previews=preview_responses
    )

# --- ENDPOINTS ---

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreateRequest,
    current_user: User = Depends(get_current_admin),
    service: ProjectService = Depends(get_project_service),
    session: Session = Depends(get_session)
):
    """
    Crea un proyecto para el usuario autenticado.
    Solo ADMIN puede crear.
    """
    try:
        project = service.create_project(
            user_id=current_user.id,
            title=project_data.title,
            category=project_data.category,
            description=project_data.description,
            thumbnail_url=project_data.thumbnail_url,
            live_url=project_data.live_url,
            repo_url=project_data.repo_url,
            featured=project_data.featured,
            work_experience_id=project_data.work_experience_id,
            technology_ids=project_data.technology_ids,
            previews=[p.model_dump() for p in project_data.previews]
        )
        return build_project_response(
            project,
            SqlAlchemyProjectTechRepository(session),
            SqlAlchemyProjectPreviewRepository(session)
        )
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

@router.get("/me", response_model=List[ProjectResponse])
def get_my_projects(
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
    session: Session = Depends(get_session)
):
    """
    Obtiene todos los proyectos del usuario autenticado.
    """
    try:
        projects = service.get_all_my_projects(current_user.id)
        tech_repo = SqlAlchemyProjectTechRepository(session)
        preview_repo = SqlAlchemyProjectPreviewRepository(session)
        return [build_project_response(p, tech_repo, preview_repo) for p in projects]
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/featured", response_model=List[ProjectResponse])
def get_my_featured_projects(
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
    session: Session = Depends(get_session)
):
    """
    Obtiene proyectos destacados del usuario autenticado.
    """
    try:
        projects = service.get_featured_my_projects(current_user.id)
        tech_repo = SqlAlchemyProjectTechRepository(session)
        preview_repo = SqlAlchemyProjectPreviewRepository(session)
        return [build_project_response(p, tech_repo, preview_repo) for p in projects]
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
    session: Session = Depends(get_session)
):
    """
    Obtiene un proyecto específico.
    """
    try:
        project = service.get_project_by_id(current_user.id, project_id)
        return build_project_response(
            project,
            SqlAlchemyProjectTechRepository(session),
            SqlAlchemyProjectPreviewRepository(session)
        )
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdateRequest,
    current_user: User = Depends(get_current_admin),
    service: ProjectService = Depends(get_project_service),
    session: Session = Depends(get_session)
):
    """
    Actualiza un proyecto del usuario autenticado.
    Solo ADMIN puede editar.
    """
    try:
        project = service.update_project(
            user_id=current_user.id,
            project_id=project_id,
            title=project_data.title,
            category=project_data.category,
            description=project_data.description,
            thumbnail_url=project_data.thumbnail_url,
            live_url=project_data.live_url,
            repo_url=project_data.repo_url,
            featured=project_data.featured,
            work_experience_id=project_data.work_experience_id,
            technology_ids=project_data.technology_ids,
            previews=[p.model_dump() for p in project_data.previews] if project_data.previews is not None else None
        )
        return build_project_response(
            project,
            SqlAlchemyProjectTechRepository(session),
            SqlAlchemyProjectPreviewRepository(session)
        )
    except ProjectNotFoundError as e:
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

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_admin),
    service: ProjectService = Depends(get_project_service)
):
    """
    Elimina (soft delete) un proyecto.
    Solo ADMIN puede eliminar.
    """
    try:
        service.delete_project(current_user.id, project_id)
        return None
    except ProjectNotFoundError as e:
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

@router.get("/public/{username}", response_model=List[ProjectResponse])
def get_public_projects(
    username: str,
    session: Session = Depends(get_session)
):
    """
    Endpoint público: Obtiene todos los proyectos de un usuario por su username.
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
        
        # Obtener proyectos
        project_repo = SqlAlchemyProjectRepository(session)
        projects = project_repo.get_all_by_profile_id(profile.id)
        
        # Construir respuestas con tecnologías y previews
        tech_repo = SqlAlchemyProjectTechRepository(session)
        preview_repo = SqlAlchemyProjectPreviewRepository(session)
        return [build_project_response(p, tech_repo, preview_repo) for p in projects]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener proyectos: {str(e)}"
        )

@router.get("/public/{username}/featured", response_model=List[ProjectResponse])
def get_public_featured_projects(
    username: str,
    session: Session = Depends(get_session)
):
    """
    Endpoint público: Obtiene los proyectos destacados de un usuario por su username.
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
        
        # Obtener proyectos destacados
        project_repo = SqlAlchemyProjectRepository(session)
        projects = project_repo.get_featured_by_profile_id(profile.id)
        
        # Construir respuestas con tecnologías y previews
        tech_repo = SqlAlchemyProjectTechRepository(session)
        preview_repo = SqlAlchemyProjectPreviewRepository(session)
        return [build_project_response(p, tech_repo, preview_repo) for p in projects]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener proyectos destacados: {str(e)}"
        )

@router.get("/public/{username}/{project_id}", response_model=ProjectResponse)
def get_public_project(
    username: str,
    project_id: int,
    session: Session = Depends(get_session)
):
    """
    Endpoint público: Obtiene un proyecto específico de un usuario por su username.
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
        
        # Obtener proyecto
        project_repo = SqlAlchemyProjectRepository(session)
        project = project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado."
            )
        
        # Verificar que el proyecto pertenezca al usuario
        if project.profile_id != profile.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado."
            )
        
        # Construir respuesta con tecnologías y previews
        tech_repo = SqlAlchemyProjectTechRepository(session)
        preview_repo = SqlAlchemyProjectPreviewRepository(session)
        return build_project_response(project, tech_repo, preview_repo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener proyecto: {str(e)}"
        )
