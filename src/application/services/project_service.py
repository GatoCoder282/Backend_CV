from datetime import datetime
from typing import List, Optional

from src.domain.entities import Project, ProjectTech, ProjectPreview, ProjectCategory
from src.domain.ports import (
	ProjectRepository,
	ProjectTechRepository,
	ProjectPreviewRepository,
	ProfileRepository,
	WorkExperienceRepository
)
from src.domain.exceptions import DomainException


class ProjectNotFoundError(DomainException):
	"""Cuando no existe el proyecto."""
	pass


class UnauthorizedAccessError(DomainException):
	"""Cuando un usuario intenta acceder a recursos que no le pertenecen."""
	pass


class ProjectService:
	def __init__(
		self,
		project_repository: ProjectRepository,
		project_tech_repository: ProjectTechRepository,
		project_preview_repository: ProjectPreviewRepository,
		profile_repository: ProfileRepository,
		work_experience_repository: WorkExperienceRepository
	):
		self.project_repository = project_repository
		self.project_tech_repository = project_tech_repository
		self.project_preview_repository = project_preview_repository
		self.profile_repository = profile_repository
		self.work_experience_repository = work_experience_repository

	def _get_my_profile(self, user_id: int):
		profile = self.profile_repository.get_by_user_id(user_id)
		if not profile:
			raise DomainException("El usuario no tiene un perfil creado.")
		return profile

	def _verify_project_ownership(self, user_id: int, project: Project):
		profile = self._get_my_profile(user_id)
		if project.profile_id != profile.id:
			raise UnauthorizedAccessError("No tienes permiso para acceder a este proyecto.")

	def _verify_work_experience_ownership(self, user_id: int, work_experience_id: Optional[int]):
		if work_experience_id is None:
			return
		work_experience = self.work_experience_repository.get_by_id(work_experience_id)
		if not work_experience:
			raise DomainException("La experiencia laboral no existe.")
		profile = self._get_my_profile(user_id)
		if work_experience.profile_id != profile.id:
			raise UnauthorizedAccessError("No tienes permiso para usar esta experiencia laboral.")

	def create_project(
		self,
		user_id: int,
		title: str,
		category: ProjectCategory,
		description: Optional[str] = None,
		thumbnail_url: Optional[str] = None,
		live_url: Optional[str] = None,
		repo_url: Optional[str] = None,
		featured: bool = False,
		work_experience_id: Optional[int] = None,
		technology_ids: Optional[List[int]] = None,
		previews: Optional[List[dict]] = None
	) -> Project:
		profile = self._get_my_profile(user_id)
		self._verify_work_experience_ownership(user_id, work_experience_id)

		new_project = Project(
			profile_id=profile.id,
			title=title,
			category=category,
			description=description,
			thumbnail_url=thumbnail_url,
			live_url=live_url,
			repo_url=repo_url,
			featured=featured,
			work_experience_id=work_experience_id,
			created_by=user_id,
			is_active=True
		)

		project = self.project_repository.save(new_project)

		# Asociar tecnologías
		for tech_id in technology_ids or []:
			self.project_tech_repository.save(
				ProjectTech(
					project_id=project.id,
					tech_id=tech_id,
					created_by=user_id,
					is_active=True
				)
			)

		# Agregar previews
		for preview in previews or []:
			self.project_preview_repository.save(
				ProjectPreview(
					project_id=project.id,
					image_url=preview["image_url"],
					caption=preview.get("caption"),
					order=preview.get("order", 0),
					created_by=user_id,
					is_active=True
				)
			)

		return project

	def get_all_my_projects(self, user_id: int) -> List[Project]:
		profile = self._get_my_profile(user_id)
		return self.project_repository.get_all_by_profile_id(profile.id)

	def get_featured_my_projects(self, user_id: int) -> List[Project]:
		profile = self._get_my_profile(user_id)
		return self.project_repository.get_featured_by_profile_id(profile.id)

	def get_project_by_id(self, user_id: int, project_id: int) -> Project:
		project = self.project_repository.get_by_id(project_id)
		if not project:
			raise ProjectNotFoundError("Proyecto no encontrado.")
		self._verify_project_ownership(user_id, project)
		return project

	def update_project(
		self,
		user_id: int,
		project_id: int,
		title: Optional[str] = None,
		category: Optional[ProjectCategory] = None,
		description: Optional[str] = None,
		thumbnail_url: Optional[str] = None,
		live_url: Optional[str] = None,
		repo_url: Optional[str] = None,
		featured: Optional[bool] = None,
		work_experience_id: Optional[int] = None,
		technology_ids: Optional[List[int]] = None,
		previews: Optional[List[dict]] = None
	) -> Project:
		existing = self.project_repository.get_by_id(project_id)
		if not existing:
			raise ProjectNotFoundError("Proyecto no encontrado.")
		self._verify_project_ownership(user_id, existing)
		self._verify_work_experience_ownership(user_id, work_experience_id)

		updated = Project(
			id=existing.id,
			profile_id=existing.profile_id,
			title=title if title is not None else existing.title,
			category=category if category is not None else existing.category,
			description=description if description is not None else existing.description,
			thumbnail_url=thumbnail_url if thumbnail_url is not None else existing.thumbnail_url,
			live_url=live_url if live_url is not None else existing.live_url,
			repo_url=repo_url if repo_url is not None else existing.repo_url,
			featured=featured if featured is not None else existing.featured,
			work_experience_id=work_experience_id if work_experience_id is not None else existing.work_experience_id,
			updated_at=datetime.now(),
			created_by=existing.created_by,
			updated_by=user_id,
			is_active=existing.is_active
		)

		project = self.project_repository.update(updated)

		# Actualizar tecnologías (reemplazo total si se envían)
		if technology_ids is not None:
			self.project_tech_repository.delete_by_project_id(project.id)
			for tech_id in technology_ids:
				self.project_tech_repository.save(
					ProjectTech(
						project_id=project.id,
						tech_id=tech_id,
						created_by=user_id,
						is_active=True
					)
				)

		# Actualizar previews (reemplazo total si se envían)
		if previews is not None:
			existing_previews = self.project_preview_repository.get_by_project_id(project.id)
			for prev in existing_previews:
				self.project_preview_repository.delete(prev.id)
			for preview in previews:
				self.project_preview_repository.save(
					ProjectPreview(
						project_id=project.id,
						image_url=preview["image_url"],
						caption=preview.get("caption"),
						order=preview.get("order", 0),
						created_by=user_id,
						is_active=True
					)
				)

		return project

	def delete_project(self, user_id: int, project_id: int) -> bool:
		existing = self.project_repository.get_by_id(project_id)
		if not existing:
			raise ProjectNotFoundError("Proyecto no encontrado.")
		self._verify_project_ownership(user_id, existing)
		return self.project_repository.delete(project_id, user_id)
