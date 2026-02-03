from typing import Optional
from src.domain.entities import User, UserRole
from src.domain.ports import UserRepository, PasswordHasher, TokenManager
from src.domain.exceptions import UserAlreadyExistsError

class AuthService:
    def __init__(
        self, 
        user_repository: UserRepository,
        hasher: PasswordHasher,      # Inyección de dependencia
        token_manager: TokenManager  # Inyección de dependencia
    ):
        self.user_repository = user_repository
        self.hasher = hasher
        self.token_manager = token_manager

    def register_user(self, username: str, email: str, password: str) -> User:
        if self.user_repository.get_by_email(email):
            raise UserAlreadyExistsError(f"El email {email} ya está registrado.")
        
        # Usamos el puerto (sin saber que es Argon2)
        hashed_password = self.hasher.hash(password)

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=UserRole.ADMIN 
        )

        return self.user_repository.save(new_user)
        
    def login_user(self, email: str, password: str) -> dict:
        """
        Retorna el Token si es exitoso.
        """
        user = self.user_repository.get_by_email(email)
        if not user:
            return None 
            
        # Verificamos password usando el puerto
        if not self.hasher.verify(password, user.password_hash):
            return None
            
        # Actualizamos login
        user.update_last_login()
        self.user_repository.update(user)
        
        # Generamos Token usando el puerto
        access_token = self.token_manager.create_access_token(
            data={"sub": user.email, "role": user.role.value}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}