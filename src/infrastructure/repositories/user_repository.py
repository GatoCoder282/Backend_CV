from typing import Optional
from sqlmodel import Session, select
from src.domain.entities import User, UserRole
from src.domain.ports import UserRepository
from src.infrastructure.data_base.models import UserModel

class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: UserModel) -> User:
        """
        Método auxiliar (Privado): Convierte de Infraestructura (Model) a Dominio (Entity).
        Esto asegura que el resto de tu app solo vea objetos puros.
        """
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            role=UserRole(model.role), # Convertimos string "admin" a Enum UserRole.ADMIN
            last_login=model.last_login,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            is_active=model.is_active
        )

    def _to_model(self, entity: User) -> UserModel:
        """
        Método auxiliar: Convierte de Dominio a Infraestructura para guardar en DB.
        """
        return UserModel(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            password_hash=entity.password_hash,
            role=entity.role.value, # Guardamos el valor del Enum ("admin")
            last_login=entity.last_login,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )

    def get_by_id(self, user_id: int) -> Optional[User]:
        statement = select(UserModel).where(UserModel.id == user_id)
        result = self.session.exec(statement).first()
        return self._to_domain(result) if result else None

    def get_by_email(self, email: str) -> Optional[User]:
        statement = select(UserModel).where(UserModel.email == email)
        result = self.session.exec(statement).first()
        return self._to_domain(result) if result else None

    def get_by_username(self, username: str) -> Optional[User]:
        statement = select(UserModel).where(UserModel.username == username)
        result = self.session.exec(statement).first()
        return self._to_domain(result) if result else None

    def save(self, user: User) -> User:
        """
        Guarda un nuevo usuario.
        IMPORTANTE: Actualiza el ID de la entidad de dominio con el generado por la DB.
        """
        user_model = self._to_model(user)
        self.session.add(user_model)
        self.session.commit()
        self.session.refresh(user_model) # Recupera el ID generado por la DB
        
        # Devolvemos una nueva instancia de dominio con el ID actualizado
        return self._to_domain(user_model)

    def update(self, user: User) -> User:
        """Actualiza un usuario existente."""
        # 1. Buscamos el registro actual en la DB
        statement = select(UserModel).where(UserModel.id == user.id)
        existing_model = self.session.exec(statement).first()
        
        if existing_model:
            # 2. Actualizamos campos
            existing_model.username = user.username
            existing_model.email = user.email
            existing_model.password_hash = user.password_hash
            existing_model.role = user.role.value
            existing_model.last_login = user.last_login
            existing_model.updated_at = user.updated_at
            existing_model.updated_by = user.updated_by
            existing_model.is_active = user.is_active
            
            # 3. Guardamos cambios
            self.session.add(existing_model)
            self.session.commit()
            self.session.refresh(existing_model)
            return self._to_domain(existing_model)
        
        return user # O lanzar una excepción si prefieres