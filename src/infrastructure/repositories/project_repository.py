from typing import Optional, List
from datetime import datetime
from sqlmodel import Session, select

from src.domain.ports import ProjectRepository, ProjectTechRepository, ProjectPreviewRepository
from src.domain.entities import Project, ProjectTech, ProjectPreview, ProjectCategory
from src.infrastructure.data_base.models import ProjectModel, ProjectTechModel, ProjectPreviewModel


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: ProjectModel) -> Project:
        """Convierte ProjectModel (SQLModel) a Project (Entidad de Dominio)."""
        return Project(
            id=model.id,
            profile_id=model.profile_id,
            title=model.title,
            category=ProjectCategory(model.category),
            description=model.description,
            thumbnail_url=model.thumbnail_url,
            live_url=model.live_url,
            repo_url=model.repo_url,
            featured=model.featured,
            work_experience_id=model.work_experience_id,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            is_active=model.is_active
        )

    def _to_model(self, entity: Project) -> ProjectModel:
        """Convierte Project (Entidad) a ProjectModel (SQLModel)."""
        return ProjectModel(
            id=entity.id,
            profile_id=entity.profile_id,
            title=entity.title,
            category=entity.category.value,  # Enum to string
            description=entity.description,
            thumbnail_url=entity.thumbnail_url,
            live_url=entity.live_url,
            repo_url=entity.repo_url,
            featured=entity.featured,
            work_experience_id=entity.work_experience_id,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """Busca un proyecto por ID (solo activos)."""
        stmt = select(ProjectModel).where(
            ProjectModel.id == project_id,
            ProjectModel.is_active == True
        )
        model = self.session.exec(stmt).first()
        return self._to_domain(model) if model else None

    def get_all_by_profile_id(self, profile_id: int) -> List[Project]:
        """Obtiene todos los proyectos activos de un perfil, ordenados por featured primero."""
        stmt = select(ProjectModel).where(
            ProjectModel.profile_id == profile_id,
            ProjectModel.is_active == True
        ).order_by(ProjectModel.featured.desc(), ProjectModel.id.desc())
        
        models = self.session.exec(stmt).all()
        return [self._to_domain(model) for model in models]

    def get_featured_by_profile_id(self, profile_id: int) -> List[Project]:
        """Obtiene solo los proyectos destacados de un perfil."""
        stmt = select(ProjectModel).where(
            ProjectModel.profile_id == profile_id,
            ProjectModel.featured == True,
            ProjectModel.is_active == True
        ).order_by(ProjectModel.id.desc())
        
        models = self.session.exec(stmt).all()
        return [self._to_domain(model) for model in models]

    def save(self, project: Project) -> Project:
        """Guarda un nuevo proyecto."""
        model = self._to_model(project)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, project: Project) -> Project:
        """Actualiza un proyecto existente."""
        stmt = select(ProjectModel).where(ProjectModel.id == project.id)
        model = self.session.exec(stmt).first()
        
        if model:
            model.title = project.title
            model.category = project.category.value
            model.description = project.description
            model.thumbnail_url = project.thumbnail_url
            model.live_url = project.live_url
            model.repo_url = project.repo_url
            model.featured = project.featured
            model.work_experience_id = project.work_experience_id
            model.updated_at = project.updated_at
            model.updated_by = project.updated_by
            
            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)
            return self._to_domain(model)
        
        raise ValueError(f"Project with id {project.id} not found")

    def delete(self, project_id: int, deleted_by: int) -> bool:
        """Soft delete de un proyecto."""
        stmt = select(ProjectModel).where(ProjectModel.id == project_id)
        model = self.session.exec(stmt).first()
        
        if model:
            model.is_active = False
            model.updated_at = datetime.now()
            model.updated_by = deleted_by
            self.session.add(model)
            self.session.commit()
            return True
        
        return False


class SqlAlchemyProjectTechRepository(ProjectTechRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: ProjectTechModel) -> ProjectTech:
        """Convierte ProjectTechModel a ProjectTech."""
        return ProjectTech(
            project_id=model.project_id,
            tech_id=model.tech_id,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            is_active=model.is_active
        )

    def _to_model(self, entity: ProjectTech) -> ProjectTechModel:
        """Convierte ProjectTech a ProjectTechModel."""
        return ProjectTechModel(
            project_id=entity.project_id,
            tech_id=entity.tech_id,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )

    def get_technologies_by_project_id(self, project_id: int) -> List[int]:
        """Obtiene los IDs de tecnologías asociadas a un proyecto (solo activas)."""
        stmt = select(ProjectTechModel).where(
            ProjectTechModel.project_id == project_id,
            ProjectTechModel.is_active == True
        )
        models = self.session.exec(stmt).all()
        return [model.tech_id for model in models]

    def save(self, project_tech: ProjectTech) -> ProjectTech:
        """Asocia una tecnología a un proyecto."""
        model = self._to_model(project_tech)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete_by_project_id(self, project_id: int) -> bool:
        """Soft delete de todas las asociaciones de tecnologías de un proyecto."""
        stmt = select(ProjectTechModel).where(
            ProjectTechModel.project_id == project_id,
            ProjectTechModel.is_active == True
        )
        models = self.session.exec(stmt).all()
        
        for model in models:
            model.is_active = False
            model.updated_at = datetime.now()
            self.session.add(model)
        
        self.session.commit()
        return True


class SqlAlchemyProjectPreviewRepository(ProjectPreviewRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: ProjectPreviewModel) -> ProjectPreview:
        """Convierte ProjectPreviewModel a ProjectPreview."""
        return ProjectPreview(
            id=model.id,
            project_id=model.project_id,
            image_url=model.image_url,
            caption=model.caption,
            order=model.order,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            is_active=model.is_active
        )

    def _to_model(self, entity: ProjectPreview) -> ProjectPreviewModel:
        """Convierte ProjectPreview a ProjectPreviewModel."""
        return ProjectPreviewModel(
            id=entity.id,
            project_id=entity.project_id,
            image_url=entity.image_url,
            caption=entity.caption,
            order=entity.order,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )

    def get_by_project_id(self, project_id: int) -> List[ProjectPreview]:
        """Obtiene todas las imágenes de preview de un proyecto, ordenadas por order."""
        stmt = select(ProjectPreviewModel).where(
            ProjectPreviewModel.project_id == project_id,
            ProjectPreviewModel.is_active == True
        ).order_by(ProjectPreviewModel.order.asc())
        
        models = self.session.exec(stmt).all()
        return [self._to_domain(model) for model in models]

    def save(self, preview: ProjectPreview) -> ProjectPreview:
        """Guarda una nueva imagen de preview."""
        model = self._to_model(preview)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, preview_id: int) -> bool:
        """Soft delete de una imagen de preview."""
        stmt = select(ProjectPreviewModel).where(ProjectPreviewModel.id == preview_id)
        model = self.session.exec(stmt).first()
        
        if model:
            model.is_active = False
            model.updated_at = datetime.now()
            self.session.add(model)
            self.session.commit()
            return True
        
        return False
