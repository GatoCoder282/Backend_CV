from typing import Optional, List
from datetime import datetime
from sqlmodel import Session, select

from src.domain.ports import TechnologyRepository
from src.domain.entities import Technology, TechnologyCategory
from src.infrastructure.data_base.models import TechnologyModel


class SqlAlchemyTechnologyRepository(TechnologyRepository):
	def __init__(self, session: Session):
		self.session = session

	def _to_domain(self, model: TechnologyModel) -> Technology:
		return Technology(
			profile_id=model.profile_id,
			id=model.id,
			name=model.name,
			category=TechnologyCategory(model.category),
			icon_url=model.icon_url,
			updated_at=model.updated_at,
			created_by=model.created_by,
			updated_by=model.updated_by,
			is_active=model.is_active
		)

	def _to_model(self, entity: Technology) -> TechnologyModel:
		return TechnologyModel(
			profile_id=entity.profile_id,
			id=entity.id,
			name=entity.name,
			category=entity.category.value,
			icon_url=entity.icon_url,
			updated_at=entity.updated_at,
			created_by=entity.created_by,
			updated_by=entity.updated_by,
			is_active=entity.is_active
		)

	def get_by_id(self, tech_id: int) -> Optional[Technology]:
		stmt = select(TechnologyModel).where(
			TechnologyModel.id == tech_id,
			TechnologyModel.is_active == True
		)
		model = self.session.exec(stmt).first()
		return self._to_domain(model) if model else None

	def get_all_by_profile_id(self, profile_id: int) -> List[Technology]:
		stmt = select(TechnologyModel).where(
			TechnologyModel.profile_id == profile_id,
			TechnologyModel.is_active == True
		).order_by(TechnologyModel.name.asc())
		models = self.session.exec(stmt).all()
		return [self._to_domain(model) for model in models]

	def save(self, technology: Technology) -> Technology:
		model = self._to_model(technology)
		self.session.add(model)
		self.session.commit()
		self.session.refresh(model)
		return self._to_domain(model)

	def update(self, technology: Technology) -> Technology:
		stmt = select(TechnologyModel).where(TechnologyModel.id == technology.id)
		model = self.session.exec(stmt).first()

		if model:
			model.profile_id = technology.profile_id
			model.name = technology.name
			model.category = technology.category.value
			model.icon_url = technology.icon_url
			model.updated_at = technology.updated_at
			model.updated_by = technology.updated_by
			self.session.add(model)
			self.session.commit()
			self.session.refresh(model)
			return self._to_domain(model)

		raise ValueError(f"Technology with id {technology.id} not found")

	def delete(self, tech_id: int, deleted_by: int) -> bool:
		stmt = select(TechnologyModel).where(TechnologyModel.id == tech_id)
		model = self.session.exec(stmt).first()

		if model:
			model.is_active = False
			model.updated_at = datetime.now()
			model.updated_by = deleted_by
			self.session.add(model)
			self.session.commit()
			return True

		return False
