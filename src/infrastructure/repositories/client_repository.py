from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.domain.ports import ClientRepository
from src.domain.entities import Client
from src.infrastructure.data_base.models import ClientModel


class SqlAlchemyClientRepository(ClientRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: ClientModel) -> Client:
        """Convierte ClientModel a Client."""
        return Client(
            id=model.id,
            profile_id=model.profile_id,
            name=model.name,
            company=model.company,
            feedback=model.feedback,
            client_photo_url=model.client_photo_url,
            project_link=model.project_link,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            is_active=model.is_active
        )

    def _to_model(self, entity: Client) -> ClientModel:
        """Convierte Client a ClientModel."""
        return ClientModel(
            id=entity.id,
            profile_id=entity.profile_id,
            name=entity.name,
            company=entity.company,
            feedback=entity.feedback,
            client_photo_url=entity.client_photo_url,
            project_link=entity.project_link,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )

    def get_by_id(self, client_id: int) -> Optional[Client]:
        """Busca un cliente por ID (solo activos)."""
        stmt = select(ClientModel).where(
            ClientModel.id == client_id,
            ClientModel.is_active == True
        )
        model = self.session.exec(stmt).first()
        return self._to_domain(model) if model else None

    def get_all_by_profile_id(self, profile_id: int) -> List[Client]:
        """Obtiene todos los clientes activos de un perfil, ordenados por nombre."""
        stmt = select(ClientModel).where(
            ClientModel.profile_id == profile_id,
            ClientModel.is_active == True
        ).order_by(ClientModel.name.asc())
        
        models = self.session.exec(stmt).all()
        return [self._to_domain(model) for model in models]

    def save(self, client: Client) -> Client:
        """Guarda un nuevo cliente."""
        model = self._to_model(client)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, client: Client) -> Client:
        """Actualiza un cliente existente."""
        stmt = select(ClientModel).where(ClientModel.id == client.id)
        model = self.session.exec(stmt).first()
        
        if model:
            model.name = client.name
            model.company = client.company
            model.feedback = client.feedback
            model.client_photo_url = client.client_photo_url
            model.project_link = client.project_link
            model.updated_at = client.updated_at
            model.updated_by = client.updated_by
            
            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)
            return self._to_domain(model)
        
        raise ValueError(f"Client with id {client.id} not found")

    def delete(self, client_id: int, deleted_by: int) -> bool:
        """Soft delete de un cliente."""
        stmt = select(ClientModel).where(ClientModel.id == client_id)
        model = self.session.exec(stmt).first()
        
        if model:
            model.is_active = False
            model.updated_at = datetime.now()
            model.updated_by = deleted_by
            self.session.add(model)
            self.session.commit()
            return True
        
        return False
