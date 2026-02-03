from datetime import datetime, date
from typing import List, Optional

from src.domain.entities import WorkExperience
from src.domain.ports import WorkExperienceRepository, ProfileRepository
from src.domain.exceptions import DomainException


class WorkExperienceNotFoundError(DomainException):
    """Cuando no existe la experiencia laboral."""
    pass


class UnauthorizedAccessError(DomainException):
    """Cuando un usuario intenta acceder a recursos que no le pertenecen."""
    pass


class WorkExperienceService:
    def __init__(
        self,
        work_experience_repository: WorkExperienceRepository,
        profile_repository: ProfileRepository
    ):
        self.work_experience_repository = work_experience_repository
        self.profile_repository = profile_repository

    def _verify_profile_ownership(self, user_id: int, profile_id: int):
        """
        Verifica que el perfil pertenezca al usuario (multi-tenant seguro).
        """
        profile = self.profile_repository.get_by_user_id(user_id)
        if not profile or profile.id != profile_id:
            raise UnauthorizedAccessError("No tienes permiso para acceder a este perfil.")

    def create_work_experience(
        self,
        user_id: int,
        job_title: str,
        company: str,
        start_date: date,
        location: Optional[str] = None,
        end_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> WorkExperience:
        """
        Crea una experiencia laboral para el perfil del usuario autenticado.
        """
        # Obtener perfil del usuario
        profile = self.profile_repository.get_by_user_id(user_id)
        if not profile:
            raise DomainException("El usuario no tiene un perfil creado.")

        new_work_experience = WorkExperience(
            profile_id=profile.id,
            job_title=job_title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            description=description,
            created_by=user_id,
            is_active=True
        )

        return self.work_experience_repository.save(new_work_experience)

    def get_all_my_work_experiences(self, user_id: int) -> List[WorkExperience]:
        """
        Obtiene todas las experiencias laborales del usuario autenticado (multi-tenant seguro).
        """
        profile = self.profile_repository.get_by_user_id(user_id)
        if not profile:
            raise DomainException("El usuario no tiene un perfil creado.")

        return self.work_experience_repository.get_all_by_profile_id(profile.id)

    def get_work_experience_by_id(self, user_id: int, work_experience_id: int) -> WorkExperience:
        """
        Obtiene una experiencia laboral específica (verifica ownership).
        """
        work_experience = self.work_experience_repository.get_by_id(work_experience_id)
        if not work_experience:
            raise WorkExperienceNotFoundError("Experiencia laboral no encontrada.")

        # Verificar que pertenece al usuario
        self._verify_profile_ownership(user_id, work_experience.profile_id)
        return work_experience

    def update_work_experience(
        self,
        user_id: int,
        work_experience_id: int,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> WorkExperience:
        """
        Actualiza una experiencia laboral (solo si pertenece al usuario).
        """
        existing = self.work_experience_repository.get_by_id(work_experience_id)
        if not existing:
            raise WorkExperienceNotFoundError("Experiencia laboral no encontrada.")

        # Verificar ownership
        self._verify_profile_ownership(user_id, existing.profile_id)

        updated_work_experience = WorkExperience(
            id=existing.id,
            profile_id=existing.profile_id,
            job_title=job_title if job_title is not None else existing.job_title,
            company=company if company is not None else existing.company,
            location=location if location is not None else existing.location,
            start_date=start_date if start_date is not None else existing.start_date,
            end_date=end_date if end_date is not None else existing.end_date,
            description=description if description is not None else existing.description,
            updated_at=datetime.now(),
            created_by=existing.created_by,
            updated_by=user_id,
            is_active=existing.is_active
        )

        return self.work_experience_repository.update(updated_work_experience)

    def delete_work_experience(self, user_id: int, work_experience_id: int) -> bool:
        """
        Elimina (soft delete) una experiencia laboral (solo si pertenece al usuario).
        """
        existing = self.work_experience_repository.get_by_id(work_experience_id)
        if not existing:
            raise WorkExperienceNotFoundError("Experiencia laboral no encontrada.")

        # Verificar ownership
        self._verify_profile_ownership(user_id, existing.profile_id)

        return self.work_experience_repository.delete(work_experience_id, user_id)
