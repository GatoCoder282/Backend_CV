import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestProfileFlow:
    """Tests de integración para el flujo completo de Profile"""

    @pytest.fixture
    def authenticated_user(self, client: TestClient):
        """Fixture: Crea y autentica un usuario ADMIN"""
        # Registro
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=register_data)
        
        # Login
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        
        return {"token": token, "email": "test@example.com"}

    def test_create_profile_success(self, client: TestClient, authenticated_user):
        """Test: Crear perfil exitosamente"""
        # Arrange
        profile_data = {
            "name": "Juan",
            "last_name": "Pérez",
            "current_title": "Full Stack Developer",
            "bio_summary": "Desarrollador apasionado por Python",
            "phone": "+591 12345678",
            "location": "Cochabamba, Bolivia",
            "photo_url": "https://example.com/photo.jpg"
        }
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        
        # Act
        response = client.post("/profile", json=profile_data, headers=headers)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Juan"
        assert data["last_name"] == "Pérez"
        assert data["email"] == authenticated_user["email"]
        assert data["current_title"] == "Full Stack Developer"
        assert data["bio_summary"] == "Desarrollador apasionado por Python"
        assert data["phone"] == "+591 12345678"
        assert data["location"] == "Cochabamba, Bolivia"
        assert data["photo_url"] == "https://example.com/photo.jpg"
        assert "id" in data

    def test_create_profile_duplicate_fails(self, client: TestClient, authenticated_user):
        """Test: No se puede crear más de un perfil por usuario"""
        # Arrange
        profile_data = {
            "name": "Juan",
            "last_name": "Pérez",
            "current_title": "Developer"
        }
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        
        # Act - Primer perfil (exitoso)
        response1 = client.post("/profile", json=profile_data, headers=headers)
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Act - Segundo perfil (debe fallar)
        response2 = client.post("/profile", json=profile_data, headers=headers)
        
        # Assert
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert "ya tiene un perfil" in response2.json()["detail"].lower()

    def test_create_profile_without_auth_fails(self, client: TestClient):
        """Test: Crear perfil sin autenticación debe fallar"""
        # Arrange
        profile_data = {
            "name": "Juan",
            "last_name": "Pérez"
        }
        
        # Act
        response = client.post("/profile", json=profile_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_profile_missing_required_fields_fails(self, client: TestClient, authenticated_user):
        """Test: Campos requeridos deben ser validados"""
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        
        # Act - Sin name
        response1 = client.post("/profile", json={
            "last_name": "Pérez"
        }, headers=headers)
        
        # Act - Sin last_name
        response2 = client.post("/profile", json={
            "name": "Juan"
        }, headers=headers)
        
        # Assert
        assert response1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_my_profile_success(self, client: TestClient, authenticated_user):
        """Test: Obtener mi perfil exitosamente"""
        # Arrange - Crear perfil primero
        profile_data = {
            "name": "María",
            "last_name": "González",
            "current_title": "Backend Developer"
        }
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        client.post("/profile", json=profile_data, headers=headers)
        
        # Act
        response = client.get("/profile/me", headers=headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "María"
        assert data["last_name"] == "González"
        assert data["current_title"] == "Backend Developer"

    def test_get_my_profile_without_creating_fails(self, client: TestClient, authenticated_user):
        """Test: Obtener perfil sin haberlo creado debe fallar"""
        # Arrange
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        
        # Act - Sin crear perfil antes
        response = client.get("/profile/me", headers=headers)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "perfil" in response.json()["detail"].lower() and "no encontrado" in response.json()["detail"].lower()

    def test_get_my_profile_without_auth_fails(self, client: TestClient):
        """Test: Obtener perfil sin autenticación debe fallar"""
        # Act
        response = client.get("/profile/me")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_my_profile_success(self, client: TestClient, authenticated_user):
        """Test: Actualizar perfil exitosamente"""
        # Arrange - Crear perfil primero
        profile_data = {
            "name": "Carlos",
            "last_name": "López",
            "current_title": "Junior Developer"
        }
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        client.post("/profile", json=profile_data, headers=headers)
        
        # Act - Actualizar
        update_data = {
            "current_title": "Senior Developer",
            "bio_summary": "Experiencia en Python, FastAPI y PostgreSQL",
            "phone": "+591 99887766"
        }
        response = client.put("/profile/me", json=update_data, headers=headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Carlos"  # No cambió
        assert data["last_name"] == "López"  # No cambió
        assert data["current_title"] == "Senior Developer"  # Actualizado
        assert data["bio_summary"] == "Experiencia en Python, FastAPI y PostgreSQL"  # Actualizado
        assert data["phone"] == "+591 99887766"  # Actualizado

    def test_update_my_profile_partial_update(self, client: TestClient, authenticated_user):
        """Test: Actualización parcial solo modifica campos enviados"""
        # Arrange - Crear perfil
        profile_data = {
            "name": "Ana",
            "last_name": "Martínez",
            "current_title": "Frontend Developer",
            "phone": "+591 11111111"
        }
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        client.post("/profile", json=profile_data, headers=headers)
        
        # Act - Actualizar solo el título
        update_data = {
            "current_title": "Full Stack Developer"
        }
        response = client.put("/profile/me", json=update_data, headers=headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["current_title"] == "Full Stack Developer"  # Actualizado
        assert data["phone"] == "+591 11111111"  # Conservado
        assert data["name"] == "Ana"  # Conservado
        assert data["last_name"] == "Martínez"  # Conservado

    def test_update_my_profile_without_creating_fails(self, client: TestClient, authenticated_user):
        """Test: Actualizar perfil sin haberlo creado debe fallar"""
        # Arrange
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        update_data = {
            "current_title": "Developer"
        }
        
        # Act - Sin crear perfil antes
        response = client.put("/profile/me", json=update_data, headers=headers)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_my_profile_without_auth_fails(self, client: TestClient):
        """Test: Actualizar perfil sin autenticación debe fallar"""
        # Arrange
        update_data = {
            "current_title": "Developer"
        }
        
        # Act
        response = client.put("/profile/me", json=update_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_multi_tenant_isolation(self, client: TestClient):
        """Test: Multi-tenant - Cada usuario solo ve su propio perfil"""
        # Arrange - Crear dos usuarios con sus perfiles
        # Usuario 1
        client.post("/auth/register", json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123"
        })
        login1 = client.post("/auth/login", data={
            "username": "user1@example.com",
            "password": "password123"
        })
        token1 = login1.json()["access_token"]
        client.post("/profile", json={
            "name": "User",
            "last_name": "One",
            "current_title": "Developer 1"
        }, headers={"Authorization": f"Bearer {token1}"})
        
        # Usuario 2
        client.post("/auth/register", json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        })
        login2 = client.post("/auth/login", data={
            "username": "user2@example.com",
            "password": "password123"
        })
        token2 = login2.json()["access_token"]
        client.post("/profile", json={
            "name": "User",
            "last_name": "Two",
            "current_title": "Developer 2"
        }, headers={"Authorization": f"Bearer {token2}"})
        
        # Act - Usuario 1 obtiene su perfil
        response1 = client.get("/profile/me", headers={"Authorization": f"Bearer {token1}"})
        
        # Act - Usuario 2 obtiene su perfil
        response2 = client.get("/profile/me", headers={"Authorization": f"Bearer {token2}"})
        
        # Assert - Cada uno solo ve el suyo
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["last_name"] == "One"
        assert data1["current_title"] == "Developer 1"
        
        assert data2["last_name"] == "Two"
        assert data2["current_title"] == "Developer 2"
        
        # Los IDs deben ser diferentes
        assert data1["id"] != data2["id"]

    def test_complete_profile_flow(self, client: TestClient):
        """Test: Flujo completo de perfil - Registro, Login, Crear, Obtener, Actualizar"""
        # Step 1: Registro
        register_data = {
            "username": "flowuser",
            "email": "flow@example.com",
            "password": "password123"
        }
        register_response = client.post("/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # Step 2: Login
        login_data = {
            "username": "flow@example.com",
            "password": "password123"
        }
        login_response = client.post("/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Crear perfil
        profile_data = {
            "name": "Flow",
            "last_name": "User",
            "current_title": "QA Engineer"
        }
        create_response = client.post("/profile", json=profile_data, headers=headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        profile_id = create_response.json()["id"]
        
        # Step 4: Obtener perfil
        get_response = client.get("/profile/me", headers=headers)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["id"] == profile_id
        assert get_response.json()["current_title"] == "QA Engineer"
        
        # Step 5: Actualizar perfil
        update_data = {
            "current_title": "Senior QA Engineer",
            "bio_summary": "Especialista en automatización de pruebas"
        }
        update_response = client.put("/profile/me", json=update_data, headers=headers)
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["current_title"] == "Senior QA Engineer"
        assert update_response.json()["bio_summary"] == "Especialista en automatización de pruebas"
        
        # Step 6: Verificar cambios persisten
        final_response = client.get("/profile/me", headers=headers)
        assert final_response.status_code == status.HTTP_200_OK
        final_data = final_response.json()
        assert final_data["current_title"] == "Senior QA Engineer"
        assert final_data["bio_summary"] == "Especialista en automatización de pruebas"
