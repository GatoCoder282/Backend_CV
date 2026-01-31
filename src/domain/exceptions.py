class DomainException(Exception):
    """Excepción base para el dominio."""
    pass

class InvalidUserError(DomainException):
    """Cuando un usuario no cumple las reglas de negocio."""
    pass

class UserAlreadyExistsError(DomainException):
    """Cuando intentas registrar un email/username duplicado."""
    pass