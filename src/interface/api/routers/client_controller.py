from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

# Imports de Infraestructura
from src.infrastructure.data_base.main import get_session
from src.infrastructure.repositories.client_repository import SqlAlchemyClientRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.user_repository import SqlAlchemyUserRepository

# Imports de Aplicación
from src.application.services.client_service import (
    ClientService,
    ClientNotFoundError,
    UnauthorizedAccessError
)
from src.application.dtos.schemas import (
    ClientCreateRequest,
    ClientUpdateRequest,
    ClientResponse
)

# Imports de Interface (Dependencias)
from src.interface.api.authorization import get_current_user, get_current_admin

# Imports de Dominio
from src.domain.entities import User
from src.domain.exceptions import InvalidUserError, DomainException

router = APIRouter(prefix="/clients", tags=["Clients"])

# --- FACTORY DE SERVICIOS ---
def get_client_service(session: Session = Depends(get_session)) -> ClientService:
    """Ensambla el servicio de clientes."""
    client_repo = SqlAlchemyClientRepository(session)
    profile_repo = SqlAlchemyProfileRepository(session)
    return ClientService(client_repo, profile_repo)

# --- ENDPOINTS ---

@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client_data: ClientCreateRequest,
    current_user: User = Depends(get_current_admin),
    service: ClientService = Depends(get_client_service)
):
    """
    Crea un cliente para el usuario autenticado.
    Solo ADMIN puede crear.
    """
    try:
        new_client = service.create_client(
            user_id=current_user.id,
            name=client_data.name,
            company=client_data.company,
            feedback=client_data.feedback,
            client_photo_url=client_data.client_photo_url,
            project_link=client_data.project_link
        )
        return new_client
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

@router.get("/me", response_model=List[ClientResponse])
def get_my_clients(
    current_user: User = Depends(get_current_user),
    service: ClientService = Depends(get_client_service)
):
    """
    Obtiene todos los clientes del usuario autenticado.
    """
    try:
        return service.get_all_my_clients(current_user.id)
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    service: ClientService = Depends(get_client_service)
):
    """
    Obtiene un cliente específico.
    """
    try:
        return service.get_client_by_id(current_user.id, client_id)
    except ClientNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_data: ClientUpdateRequest,
    current_user: User = Depends(get_current_admin),
    service: ClientService = Depends(get_client_service)
):
    """
    Actualiza un cliente del usuario autenticado.
    Solo ADMIN puede editar.
    """
    try:
        updated = service.update_client(
            user_id=current_user.id,
            client_id=client_id,
            name=client_data.name,
            company=client_data.company,
            feedback=client_data.feedback,
            client_photo_url=client_data.client_photo_url,
            project_link=client_data.project_link
        )
        return updated
    except ClientNotFoundError as e:
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

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_admin),
    service: ClientService = Depends(get_client_service)
):
    """
    Elimina (soft delete) un cliente.
    Solo ADMIN puede eliminar.
    """
    try:
        service.delete_client(current_user.id, client_id)
        return None
    except ClientNotFoundError as e:
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

@router.get("/public/{username}", response_model=List[ClientResponse])
def get_public_clients(
    username: str,
    session: Session = Depends(get_session)
):
    """
    Endpoint público: Obtiene todos los clientes de un usuario por su username.
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
        
        # Obtener clientes
        client_repo = SqlAlchemyClientRepository(session)
        clients = client_repo.get_all_by_profile_id(profile.id)
        
        return clients
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener clientes: {str(e)}"
        )
