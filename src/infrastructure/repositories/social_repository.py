from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.domain.ports import SocialRepository
from src.domain.entities import Social
from src.infrastructure.data_base.models import SocialModel


class SqlAlchemySocialRepository(SocialRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: SocialModel) -> Social:
        """Convierte SocialModel a Social."""
        return Social(
            id=model.id,
            profile_id=model.profile_id,
            platform=model.platform,
            url=model.url,
            icon_name=model.icon_name,
            order=model.order,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            is_active=model.is_active
        )

    def _to_model(self, entity: Social) -> SocialModel:
        """Convierte Social a SocialModel."""
        return SocialModel(
            id=entity.id,
            profile_id=entity.profile_id,
            platform=entity.platform,
            url=entity.url,
            icon_name=entity.icon_name,
            order=entity.order,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )

    def get_by_id(self, social_id: int) -> Optional[Social]:
        """Busca un social link por ID (solo activos)."""
        stmt = select(SocialModel).where(
            SocialModel.id == social_id,
            SocialModel.is_active == True
        )
        model = self.session.exec(stmt).first()
        return self._to_domain(model) if model else None

    def get_all_by_profile_id(self, profile_id: int) -> List[Social]:
        """Obtiene todos los social links activos de un perfil, ordenados por orden."""
        stmt = select(SocialModel).where(
            SocialModel.profile_id == profile_id,
            SocialModel.is_active == True
        ).order_by(SocialModel.order.asc())

        models = self.session.exec(stmt).all()
        return [self._to_domain(model) for model in models]

    def save(self, social: Social) -> Social:
        """Guarda un nuevo social link."""
        model = self._to_model(social)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, social: Social) -> Social:
        """Actualiza un social link existente."""
        stmt = select(SocialModel).where(SocialModel.id == social.id)
        model = self.session.exec(stmt).first()

        if model:
            model.profile_id = social.profile_id
            model.platform = social.platform
            model.url = social.url
            model.icon_name = social.icon_name
            model.order = social.order
            model.updated_at = social.updated_at
            model.updated_by = social.updated_by

            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)
            return self._to_domain(model)

        raise ValueError(f"Social with id {social.id} not found")

    def delete(self, social_id: int, deleted_by: int) -> bool:
        """Soft delete de un social link."""
        stmt = select(SocialModel).where(SocialModel.id == social_id)
        model = self.session.exec(stmt).first()

        if model:
            model.is_active = False
            model.updated_at = datetime.now()
            model.updated_by = deleted_by
            self.session.add(model)
            self.session.commit()
            return True

        return False
