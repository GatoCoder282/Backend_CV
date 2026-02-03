from datetime import datetime
from typing import List, Optional

from src.domain.entities import Social
from src.domain.ports import SocialRepository, ProfileRepository
from src.domain.exceptions import DomainException


class SocialNotFoundError(DomainException):
	"""Cuando no existe el social link."""
	pass


class UnauthorizedAccessError(DomainException):
	"""Cuando un usuario intenta acceder a recursos que no le pertenecen."""
	pass


class SocialService:
	def __init__(self, social_repository: SocialRepository, profile_repository: ProfileRepository):
		self.social_repository = social_repository
		self.profile_repository = profile_repository

	def _get_my_profile(self, user_id: int):
		profile = self.profile_repository.get_by_user_id(user_id)
		if not profile:
			raise DomainException("El usuario no tiene un perfil creado.")
		return profile

	def _verify_social_ownership(self, user_id: int, social: Social):
		profile = self._get_my_profile(user_id)
		if social.profile_id != profile.id:
			raise UnauthorizedAccessError("No tienes permiso para acceder a este social link.")

	def create_social(
		self,
		user_id: int,
		platform: str,
		url: str,
		icon_name: Optional[str] = None,
		order: int = 0
	) -> Social:
		profile = self._get_my_profile(user_id)

		new_social = Social(
			profile_id=profile.id,
			platform=platform,
			url=url,
			icon_name=icon_name,
			order=order,
			created_by=user_id,
			is_active=True
		)

		return self.social_repository.save(new_social)

	def get_all_my_socials(self, user_id: int) -> List[Social]:
		profile = self._get_my_profile(user_id)
		return self.social_repository.get_all_by_profile_id(profile.id)

	def get_social_by_id(self, user_id: int, social_id: int) -> Social:
		social = self.social_repository.get_by_id(social_id)
		if not social:
			raise SocialNotFoundError("Social link no encontrado.")
		self._verify_social_ownership(user_id, social)
		return social

	def update_social(
		self,
		user_id: int,
		social_id: int,
		platform: Optional[str] = None,
		url: Optional[str] = None,
		icon_name: Optional[str] = None,
		order: Optional[int] = None,
		is_active: Optional[bool] = None
	) -> Social:
		existing = self.social_repository.get_by_id(social_id)
		if not existing:
			raise SocialNotFoundError("Social link no encontrado.")
		self._verify_social_ownership(user_id, existing)

		updated = Social(
			id=existing.id,
			profile_id=existing.profile_id,
			platform=platform if platform is not None else existing.platform,
			url=url if url is not None else existing.url,
			icon_name=icon_name if icon_name is not None else existing.icon_name,
			order=order if order is not None else existing.order,
			updated_at=datetime.now(),
			created_by=existing.created_by,
			updated_by=user_id,
			is_active=is_active if is_active is not None else existing.is_active
		)

		return self.social_repository.update(updated)

	def delete_social(self, user_id: int, social_id: int) -> bool:
		existing = self.social_repository.get_by_id(social_id)
		if not existing:
			raise SocialNotFoundError("Social link no encontrado.")
		self._verify_social_ownership(user_id, existing)
		return self.social_repository.delete(social_id, user_id)
