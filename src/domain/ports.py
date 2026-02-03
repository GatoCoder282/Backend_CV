from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from .entities import User, Profile, WorkExperience
from datetime import timedelta

class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca un usuario por su ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Busca un usuario por su email."""
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Busca un usuario por su username."""
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        """Guarda un nuevo usuario y lo devuelve con su ID generado."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Actualiza un usuario existente."""
        pass

class ProfileRepository(ABC):
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[Profile]:
        pass

    @abstractmethod
    def save(self, profile: Profile) -> Profile:
        pass
        
    @abstractmethod
    def update(self, profile: Profile) -> Profile:
        pass

class WorkExperienceRepository(ABC):
    @abstractmethod
    def get_by_id(self, work_experience_id: int) -> Optional[WorkExperience]:
        """Busca una experiencia laboral por ID."""
        pass

    @abstractmethod
    def get_all_by_profile_id(self, profile_id: int) -> List[WorkExperience]:
        """Obtiene todas las experiencias laborales de un perfil."""
        pass

    @abstractmethod
    def save(self, work_experience: WorkExperience) -> WorkExperience:
        """Guarda una nueva experiencia laboral."""
        pass

    @abstractmethod
    def update(self, work_experience: WorkExperience) -> WorkExperience:
        """Actualiza una experiencia laboral existente."""
        pass

    @abstractmethod
    def delete(self, work_experience_id: int, deleted_by: int) -> bool:
        """Soft delete de una experiencia laboral."""
        pass

# Puerto para Hashing (Argon2 vivirá detrás de esto)
class PasswordHasher(ABC):
    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        pass

    @abstractmethod
    def hash(self, password: str) -> str:
        pass

# Puerto para Tokens (JWT vivirá detrás de esto)
class TokenManager(ABC):
    @abstractmethod
    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        pass
    
    @abstractmethod
    def decode_token(self, token: str) -> Dict:
        pass