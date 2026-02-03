from datetime import datetime
from typing import Optional

from src.domain.entities import Profile
from src.domain.ports import ProfileRepository
from src.domain.exceptions import DomainException


class ProfileAlreadyExistsError(DomainException):
	"""Cuando un usuario intenta crear un segundo perfil."""
	pass


class ProfileNotFoundError(DomainException):
	"""Cuando no existe un perfil para el usuario."""
	pass


class ProfileService:
	def __init__(self, profile_repository: ProfileRepository):
		self.profile_repository = profile_repository

	def create_profile(
		self,
		user_id: int,
		name: str,
		last_name: str,
		email: str,
		current_title: Optional[str] = None,
		bio_summary: Optional[str] = None,
		phone: Optional[str] = None,
		location: Optional[str] = None,
		photo_url: Optional[str] = None,
		created_by: Optional[int] = None,
		is_active: bool = True
	) -> Profile:
		"""
		Crea un único perfil por usuario.
		"""
		if self.profile_repository.get_by_user_id(user_id):
			raise ProfileAlreadyExistsError("El usuario ya tiene un perfil creado.")

		new_profile = Profile(
			user_id=user_id,
			name=name,
			last_name=last_name,
			email=email,
			current_title=current_title,
			bio_summary=bio_summary,
			phone=phone,
			location=location,
			photo_url=photo_url,
			created_by=created_by or user_id,
			is_active=is_active
		)

		return self.profile_repository.save(new_profile)

	def get_my_profile(self, user_id: int) -> Profile:
		"""
		Obtiene el perfil del usuario autenticado (multi-tenant seguro).
		"""
		profile = self.profile_repository.get_by_user_id(user_id)
		if not profile:
			raise ProfileNotFoundError("Perfil no encontrado.")
		return profile

	def update_my_profile(
		self,
		user_id: int,
		name: Optional[str] = None,
		last_name: Optional[str] = None,
		email: Optional[str] = None,
		current_title: Optional[str] = None,
		bio_summary: Optional[str] = None,
		phone: Optional[str] = None,
		location: Optional[str] = None,
		photo_url: Optional[str] = None,
		is_active: Optional[bool] = None
	) -> Profile:
		"""
		Actualiza solo el perfil del usuario autenticado.
		"""
		existing = self.profile_repository.get_by_user_id(user_id)
		if not existing:
			raise ProfileNotFoundError("Perfil no encontrado.")

		updated_profile = Profile(
			id=existing.id,
			user_id=existing.user_id,
			name=name if name is not None else existing.name,
			last_name=last_name if last_name is not None else existing.last_name,
			email=email if email is not None else existing.email,
			current_title=current_title if current_title is not None else existing.current_title,
			bio_summary=bio_summary if bio_summary is not None else existing.bio_summary,
			phone=phone if phone is not None else existing.phone,
			location=location if location is not None else existing.location,
			photo_url=photo_url if photo_url is not None else existing.photo_url,
			created_at=existing.created_at,
			updated_at=datetime.now(),
			created_by=existing.created_by,
			updated_by=user_id,
			is_active=is_active if is_active is not None else existing.is_active
		)

		return self.profile_repository.update(updated_profile)
