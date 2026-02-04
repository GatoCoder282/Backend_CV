import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestAuthenticationFlow:
    """Tests de integración para el flujo completo de autenticación"""

    def test_register_new_user_success(self, client: TestClient):
        """Test: Registro exitoso de un nuevo usuario"""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "admin"  # Por defecto debe ser ADMIN (para usar su CMS)
        assert "id" in data
        assert "password" not in data  # Nunca debe devolver el password

    def test_register_duplicate_email_fails(self, client: TestClient):
        """Test: No se puede registrar el mismo email dos veces"""
        # Arrange
        user_data = {
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "password123"
        }
        
        # Act - Primer registro (exitoso)
        response1 = client.post("/auth/register", json=user_data)
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Act - Segundo registro con mismo email (debe fallar)
        user_data2 = {
            "username": "user2",
            "email": "duplicate@example.com",  # Email duplicado
            "password": "password456"
        }
        response2 = client.post("/auth/register", json=user_data2)
        
        # Assert
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response2.json()["detail"].lower() and "registrado" in response2.json()["detail"].lower()

    def test_register_duplicate_username_fails(self, client: TestClient):
        """Test: No se puede registrar el mismo username dos veces"""
        # Arrange
        user_data1 = {
            "username": "duplicateuser",
            "email": "user1@example.com",
            "password": "password123"
        }
        
        # Act - Primer registro (exitoso)
        response1 = client.post("/auth/register", json=user_data1)
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Act - Segundo registro con mismo username (debe fallar)
        user_data2 = {
            "username": "duplicateuser",  # Username duplicado
            "email": "user2@example.com",
            "password": "password456"
        }
        response2 = client.post("/auth/register", json=user_data2)
        
        # Assert
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response2.json()["detail"].lower() and "registrado" in response2.json()["detail"].lower()

    def test_register_invalid_email_fails(self, client: TestClient):
        """Test: Email inválido debe ser rechazado por validación"""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "invalid-email",  # Email sin formato válido
            "password": "password123"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password_fails(self, client: TestClient):
        """Test: Password muy corto debe ser rechazado"""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345"  # Menor a 6 caracteres
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self, client: TestClient):
        """Test: Login exitoso devuelve access token"""
        # Arrange - Primero registrar un usuario
        register_data = {
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=register_data)
        
        # Act - Login con form data (OAuth2PasswordRequestForm)
        login_data = {
            "username": "login@example.com",  # En OAuth2, el email va en 'username'
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)  # data, no json
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password_fails(self, client: TestClient):
        """Test: Login con password incorrecta debe fallar"""
        # Arrange
        register_data = {
            "username": "user",
            "email": "user@example.com",
            "password": "correctpassword"
        }
        client.post("/auth/register", json=register_data)
        
        # Act - Intentar login con password incorrecta
        login_data = {
            "username": "user@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "credenciales incorrectas" in response.json()["detail"].lower()

    def test_login_nonexistent_user_fails(self, client: TestClient):
        """Test: Login con usuario inexistente debe fallar"""
        # Act
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_with_valid_token(self, client: TestClient):
        """Test: Obtener datos del usuario autenticado con token válido"""
        # Arrange - Registrar y hacer login
        register_data = {
            "username": "authuser",
            "email": "auth@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=register_data)
        
        login_response = client.post("/auth/login", data={
            "username": "auth@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Act - Obtener datos del usuario autenticado
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "authuser"
        assert data["email"] == "auth@example.com"
        assert data["role"] == "admin"

    def test_get_current_user_without_token_fails(self, client: TestClient):
        """Test: Acceder a endpoint protegido sin token debe fallar"""
        # Act
        response = client.get("/auth/me")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_with_invalid_token_fails(self, client: TestClient):
        """Test: Token inválido debe ser rechazado"""
        # Act
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_complete_authentication_flow(self, client: TestClient):
        """Test: Flujo completo de registro, login y acceso a recurso protegido"""
        # Step 1: Registro
        register_data = {
            "username": "flowuser",
            "email": "flow@example.com",
            "password": "password123"
        }
        register_response = client.post("/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["id"]
        
        # Step 2: Login
        login_data = {
            "username": "flow@example.com",
            "password": "password123"
        }
        login_response = client.post("/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        
        # Step 3: Acceder a recurso protegido
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == status.HTTP_200_OK
        user_data = me_response.json()
        assert user_data["id"] == user_id
        assert user_data["username"] == "flowuser"
        assert user_data["email"] == "flow@example.com"

    def test_register_missing_required_fields_fails(self, client: TestClient):
        """Test: Registro sin campos requeridos debe fallar"""
        # Act - Intentar registrar sin username
        response1 = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        # Act - Intentar registrar sin email
        response2 = client.post("/auth/register", json={
            "username": "testuser",
            "password": "password123"
        })
        
        # Act - Intentar registrar sin password
        response3 = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com"
        })
        
        # Assert
        assert response1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response3.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_superadmin_with_env_email(self, client: TestClient, monkeypatch):
        """Test: Registro con email de SUPERADMIN_EMAIL crea usuario SUPERADMIN"""
        # Arrange - Configurar variable de entorno
        monkeypatch.setenv("SUPERADMIN_EMAIL", "superadmin@example.com")
        
        user_data = {
            "username": "superuser",
            "email": "superadmin@example.com",
            "password": "password123"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "superuser"
        assert data["email"] == "superadmin@example.com"
        assert data["role"] == "superadmin"  # Debe ser SUPERADMIN porque email coincide
        
    def test_register_normal_user_creates_admin(self, client: TestClient):
        """Test: Registro con email normal crea usuario ADMIN"""
        # Arrange
        user_data = {
            "username": "normaluser",
            "email": "normal@example.com",
            "password": "password123"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["role"] == "admin"  # Usuarios normales son ADMIN
