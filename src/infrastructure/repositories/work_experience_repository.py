from typing import Optional, List
from sqlmodel import Session, select
from src.domain.entities import WorkExperience
from src.domain.ports import WorkExperienceRepository as WorkExperiencePort
from src.infrastructure.data_base.models import WorkExperienceModel


class WorkExperienceRepository(WorkExperiencePort):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: WorkExperienceModel) -> WorkExperience:
        """Convierte de Model a Entity."""
        return WorkExperience(
            id=model.id,
            profile_id=model.profile_id,
            job_title=model.job_title,
            company=model.company,
            location=model.location,
            start_date=model.start_date,
            end_date=model.end_date,
            description=model.description,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            is_active=model.is_active
        )

    def _to_model(self, entity: WorkExperience) -> WorkExperienceModel:
        """Convierte de Entity a Model."""
        return WorkExperienceModel(
            id=entity.id,
            profile_id=entity.profile_id,
            job_title=entity.job_title,
            company=entity.company,
            location=entity.location,
            start_date=entity.start_date,
            end_date=entity.end_date,
            description=entity.description,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )

    def get_by_id(self, work_experience_id: int) -> Optional[WorkExperience]:
        """Busca una experiencia laboral por ID."""
        statement = select(WorkExperienceModel).where(WorkExperienceModel.id == work_experience_id)
        result = self.session.exec(statement).first()
        return self._to_domain(result) if result else None

    def get_all_by_profile_id(self, profile_id: int) -> List[WorkExperience]:
        """Obtiene todas las experiencias laborales de un perfil (multi-tenant seguro)."""
        statement = select(WorkExperienceModel).where(
            WorkExperienceModel.profile_id == profile_id,
            WorkExperienceModel.is_active == True
        ).order_by(WorkExperienceModel.start_date.desc())
        results = self.session.exec(statement).all()
        return [self._to_domain(model) for model in results]

    def save(self, work_experience: WorkExperience) -> WorkExperience:
        """Guarda una nueva experiencia laboral."""
        model = self._to_model(work_experience)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, work_experience: WorkExperience) -> WorkExperience:
        """Actualiza una experiencia laboral existente."""
        statement = select(WorkExperienceModel).where(WorkExperienceModel.id == work_experience.id)
        existing_model = self.session.exec(statement).first()

        if existing_model:
            existing_model.job_title = work_experience.job_title
            existing_model.company = work_experience.company
            existing_model.location = work_experience.location
            existing_model.start_date = work_experience.start_date
            existing_model.end_date = work_experience.end_date
            existing_model.description = work_experience.description
            existing_model.updated_at = work_experience.updated_at
            existing_model.updated_by = work_experience.updated_by
            existing_model.is_active = work_experience.is_active

            self.session.add(existing_model)
            self.session.commit()
            self.session.refresh(existing_model)
            return self._to_domain(existing_model)

        return work_experience

    def delete(self, work_experience_id: int, deleted_by: int) -> bool:
        """Soft delete de una experiencia laboral."""
        statement = select(WorkExperienceModel).where(WorkExperienceModel.id == work_experience_id)
        model = self.session.exec(statement).first()

        if model:
            from datetime import datetime
            model.is_active = False
            model.updated_by = deleted_by
            model.updated_at = datetime.now()
            self.session.add(model)
            self.session.commit()
            return True

        return False
