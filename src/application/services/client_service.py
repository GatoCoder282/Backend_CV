from datetime import datetime
from typing import List, Optional

from src.domain.entities import Client
from src.domain.ports import ClientRepository, ProfileRepository
from src.domain.exceptions import DomainException


class ClientNotFoundError(DomainException):
	"""Cuando no existe el cliente."""
	pass


class UnauthorizedAccessError(DomainException):
	"""Cuando un usuario intenta acceder a recursos que no le pertenecen."""
	pass


class ClientService:
	def __init__(self, client_repository: ClientRepository, profile_repository: ProfileRepository):
		self.client_repository = client_repository
		self.profile_repository = profile_repository

	def _get_my_profile(self, user_id: int):
		profile = self.profile_repository.get_by_user_id(user_id)
		if not profile:
			raise DomainException("El usuario no tiene un perfil creado.")
		return profile

	def _verify_client_ownership(self, user_id: int, client: Client):
		profile = self._get_my_profile(user_id)
		if client.profile_id != profile.id:
			raise UnauthorizedAccessError("No tienes permiso para acceder a este cliente.")

	def create_client(
		self,
		user_id: int,
		name: str,
		company: Optional[str] = None,
		feedback: Optional[str] = None,
		client_photo_url: Optional[str] = None,
		project_link: Optional[str] = None
	) -> Client:
		profile = self._get_my_profile(user_id)

		new_client = Client(
			profile_id=profile.id,
			name=name,
			company=company,
			feedback=feedback,
			client_photo_url=client_photo_url,
			project_link=project_link,
			created_by=user_id,
			is_active=True
		)

		return self.client_repository.save(new_client)

	def get_all_my_clients(self, user_id: int) -> List[Client]:
		profile = self._get_my_profile(user_id)
		return self.client_repository.get_all_by_profile_id(profile.id)

	def get_client_by_id(self, user_id: int, client_id: int) -> Client:
		client = self.client_repository.get_by_id(client_id)
		if not client:
			raise ClientNotFoundError("Cliente no encontrado.")
		self._verify_client_ownership(user_id, client)
		return client

	def update_client(
		self,
		user_id: int,
		client_id: int,
		name: Optional[str] = None,
		company: Optional[str] = None,
		feedback: Optional[str] = None,
		client_photo_url: Optional[str] = None,
		project_link: Optional[str] = None,
		is_active: Optional[bool] = None
	) -> Client:
		existing = self.client_repository.get_by_id(client_id)
		if not existing:
			raise ClientNotFoundError("Cliente no encontrado.")
		self._verify_client_ownership(user_id, existing)

		updated = Client(
			id=existing.id,
			profile_id=existing.profile_id,
			name=name if name is not None else existing.name,
			company=company if company is not None else existing.company,
			feedback=feedback if feedback is not None else existing.feedback,
			client_photo_url=client_photo_url if client_photo_url is not None else existing.client_photo_url,
			project_link=project_link if project_link is not None else existing.project_link,
			updated_at=datetime.now(),
			created_by=existing.created_by,
			updated_by=user_id,
			is_active=is_active if is_active is not None else existing.is_active
		)

		return self.client_repository.update(updated)

	def delete_client(self, user_id: int, client_id: int) -> bool:
		existing = self.client_repository.get_by_id(client_id)
		if not existing:
			raise ClientNotFoundError("Cliente no encontrado.")
		self._verify_client_ownership(user_id, existing)
		return self.client_repository.delete(client_id, user_id)
