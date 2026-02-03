from datetime import datetime
from typing import List, Optional

from src.domain.entities import Technology, TechnologyCategory
from src.domain.ports import TechnologyRepository, ProfileRepository
from src.domain.exceptions import DomainException


class TechnologyNotFoundError(DomainException):
	"""Cuando no existe la tecnología."""
	pass


class UnauthorizedAccessError(DomainException):
	"""Cuando un usuario intenta acceder a recursos que no le pertenecen."""
	pass


class TechnologyService:
	def __init__(self, technology_repository: TechnologyRepository, profile_repository: ProfileRepository):
		self.technology_repository = technology_repository
		self.profile_repository = profile_repository

	def _get_my_profile(self, user_id: int):
		profile = self.profile_repository.get_by_user_id(user_id)
		if not profile:
			raise DomainException("El usuario no tiene un perfil creado.")
		return profile

	def _verify_technology_ownership(self, user_id: int, technology: Technology):
		profile = self._get_my_profile(user_id)
		if technology.profile_id != profile.id:
			raise UnauthorizedAccessError("No tienes permiso para acceder a esta tecnología.")

	def create_technology(
		self,
		user_id: int,
		name: str,
		category: TechnologyCategory,
		icon_url: Optional[str] = None
	) -> Technology:
		profile = self._get_my_profile(user_id)

		new_technology = Technology(
			profile_id=profile.id,
			name=name,
			category=category,
			icon_url=icon_url,
			created_by=user_id,
			is_active=True
		)

		return self.technology_repository.save(new_technology)

	def get_all_my_technologies(self, user_id: int) -> List[Technology]:
		profile = self._get_my_profile(user_id)
		return self.technology_repository.get_all_by_profile_id(profile.id)

	def get_technology_by_id(self, user_id: int, tech_id: int) -> Technology:
		technology = self.technology_repository.get_by_id(tech_id)
		if not technology:
			raise TechnologyNotFoundError("Tecnología no encontrada.")

		self._verify_technology_ownership(user_id, technology)
		return technology

	def update_technology(
		self,
		user_id: int,
		tech_id: int,
		name: Optional[str] = None,
		category: Optional[TechnologyCategory] = None,
		icon_url: Optional[str] = None,
		is_active: Optional[bool] = None
	) -> Technology:
		existing = self.technology_repository.get_by_id(tech_id)
		if not existing:
			raise TechnologyNotFoundError("Tecnología no encontrada.")

		self._verify_technology_ownership(user_id, existing)

		updated = Technology(
			id=existing.id,
			profile_id=existing.profile_id,
			name=name if name is not None else existing.name,
			category=category if category is not None else existing.category,
			icon_url=icon_url if icon_url is not None else existing.icon_url,
			updated_at=datetime.now(),
			created_by=existing.created_by,
			updated_by=user_id,
			is_active=is_active if is_active is not None else existing.is_active
		)

		return self.technology_repository.update(updated)

	def delete_technology(self, user_id: int, tech_id: int) -> bool:
		existing = self.technology_repository.get_by_id(tech_id)
		if not existing:
			raise TechnologyNotFoundError("Tecnología no encontrada.")

		self._verify_technology_ownership(user_id, existing)
		return self.technology_repository.delete(tech_id, user_id)
