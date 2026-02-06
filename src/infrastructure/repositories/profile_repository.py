from typing import Optional
from sqlmodel import Session, select
from src.domain.entities import Profile
from src.domain.ports import ProfileRepository
from src.infrastructure.data_base.models import ProfileModel


class SqlAlchemyProfileRepository(ProfileRepository):
	def __init__(self, session: Session):
		self.session = session

	def _to_domain(self, model: ProfileModel) -> Profile:
		return Profile(
			id=model.id,
			user_id=model.user_id,
			name=model.name,
			last_name=model.last_name,
			email=model.email,
			current_title=model.current_title,
			bio_summary=model.bio_summary,
			phone=model.phone,
			location=model.location,
			photo_url=model.photo_url,
			profile=model.profile,
			created_at=model.created_at,
			updated_at=model.updated_at,
			created_by=model.created_by,
			updated_by=model.updated_by,
			is_active=model.is_active
		)

	def _to_model(self, entity: Profile) -> ProfileModel:
		return ProfileModel(
			id=entity.id,
			user_id=entity.user_id,
			name=entity.name,
			last_name=entity.last_name,
			email=entity.email,
			current_title=entity.current_title,
			bio_summary=entity.bio_summary,
			phone=entity.phone,
			location=entity.location,
			photo_url=entity.photo_url,
			profile=entity.profile,
			created_at=entity.created_at,
			updated_at=entity.updated_at,
			created_by=entity.created_by,
			updated_by=entity.updated_by,
			is_active=entity.is_active
		)

	def get_by_user_id(self, user_id: int) -> Optional[Profile]:
		statement = select(ProfileModel).where(ProfileModel.user_id == user_id)
		result = self.session.exec(statement).first()
		return self._to_domain(result) if result else None

	def save(self, profile: Profile) -> Profile:
		profile_model = self._to_model(profile)
		self.session.add(profile_model)
		self.session.commit()
		self.session.refresh(profile_model)
		return self._to_domain(profile_model)

	def update(self, profile: Profile) -> Profile:
		if profile.id is not None:
			statement = select(ProfileModel).where(ProfileModel.id == profile.id)
		else:
			statement = select(ProfileModel).where(ProfileModel.user_id == profile.user_id)

		existing_model = self.session.exec(statement).first()
		
        
		if existing_model:
			existing_model.name = profile.name
			existing_model.last_name = profile.last_name
			existing_model.email = profile.email
			existing_model.current_title = profile.current_title
			existing_model.bio_summary = profile.bio_summary
			existing_model.phone = profile.phone
			existing_model.location = profile.location
			existing_model.photo_url = profile.photo_url
			existing_model.profile = profile.profile
			existing_model.updated_at = profile.updated_at
			existing_model.updated_by = profile.updated_by
			existing_model.is_active = profile.is_active

			self.session.add(existing_model)
			self.session.commit()
			self.session.refresh(existing_model)
			return self._to_domain(existing_model)

		return profile
