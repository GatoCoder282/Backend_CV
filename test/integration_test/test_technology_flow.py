"""
Tests de Integración - Technology Flow

Valida el flujo completo de operaciones CRUD de tecnologías:
- Creación con autenticación y multi-tenant
- Listado de tecnologías propias
- Obtención por ID con validación de ownership
- Actualización con ownership validation
- Eliminación (soft delete) con ownership validation
- Aislamiento multi-tenant entre usuarios
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestTechnologyFlow:
    """Suite de tests para el flujo completo de Technology"""

    # --- FIXTURES HELPERS ---
    
    @pytest.fixture
    def authenticated_user(self, client: TestClient):
        """Usuario registrado y autenticado"""
        user_data = {
            "username": "tech_user",
            "email": "tech@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "username": "tech@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        return {"email": "tech@example.com", "token": token}

    @pytest.fixture
    def user_with_profile(self, client: TestClient, authenticated_user):
        """Usuario con perfil creado (requerido para tecnologías)"""
        profile_data = {
            "name": "Tech",
            "last_name": "Expert",
            "current_title": "Full Stack Developer"
        }
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        client.post("/profile", json=profile_data, headers=headers)
        return authenticated_user

    @pytest.fixture
    def second_user_with_profile(self, client: TestClient):
        """Segundo usuario para pruebas multi-tenant"""
        user_data = {
            "username": "tech_user2",
            "email": "tech2@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "username": "tech2@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        
        # Crear perfil
        profile_data = {
            "name": "Tech2",
            "last_name": "Expert2",
            "current_title": "Backend Developer"
        }
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/profile", json=profile_data, headers=headers)
        
        return {"email": "tech2@example.com", "token": token}

    # --- TESTS DE CREACIÓN ---

    def test_create_technology_success(self, client: TestClient, user_with_profile):
        """Test: Crear tecnología exitosamente"""
        # Arrange
        tech_data = {
            "name": "Python",
            "category": "backend",
            "icon_url": "https://icon.com/python.svg"
        }
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

        # Act
        response = client.post("/technologies", json=tech_data, headers=headers)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Python"
        assert data["category"] == "backend"
        assert data["icon_url"] == "https://icon.com/python.svg"
        assert "id" in data
        assert "profile_id" in data

    def test_create_technology_without_profile_fails(self, client: TestClient, authenticated_user):
        """Test: Crear tecnología sin perfil falla"""
        # Arrange
        tech_data = {
            "name": "JavaScript",
            "category": "frontend"
        }
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}

        # Act
        response = client.post("/technologies", json=tech_data, headers=headers)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "perfil" in response.json()["detail"].lower()

    def test_create_technology_without_auth_fails(self, client: TestClient):
        """Test: Crear tecnología sin autenticación falla"""
        # Arrange
        tech_data = {
            "name": "React",
            "category": "frontend"
        }

        # Act
        response = client.post("/technologies", json=tech_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_technology_missing_required_fields_fails(self, client: TestClient, user_with_profile):
        """Test: Crear tecnología sin campos requeridos falla"""
        # Arrange
        tech_data = {
            "name": "Angular"
            # Falta category (requerido)
        }
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

        # Act
        response = client.post("/technologies", json=tech_data, headers=headers)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_technology_invalid_category_fails(self, client: TestClient, user_with_profile):
        """Test: Crear tecnología con categoría inválida falla"""
        # Arrange
        tech_data = {
            "name": "Vue",
            "category": "invalid_category"
        }
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

        # Act
        response = client.post("/technologies", json=tech_data, headers=headers)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_technology_without_icon_url_success(self, client: TestClient, user_with_profile):
        """Test: Crear tecnología sin icon_url (opcional) es exitoso"""
        # Arrange
        tech_data = {
            "name": "Docker",
            "category": "dev_tools"
        }
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

        # Act
        response = client.post("/technologies", json=tech_data, headers=headers)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Docker"
        assert data["icon_url"] is None

    # --- TESTS DE LISTADO ---

    def test_get_my_technologies_success(self, client: TestClient, user_with_profile):
        """Test: Obtener lista de mis tecnologías"""
        # Arrange - Crear dos tecnologías
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
        client.post("/technologies", json={"name": "Python", "category": "backend"}, headers=headers)
        client.post("/technologies", json={"name": "FastAPI", "category": "backend"}, headers=headers)

        # Act
        response = client.get("/technologies/me", headers=headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        # Las tecnologías se ordenan alfabéticamente
        assert data[0]["name"] == "FastAPI"
        assert data[1]["name"] == "Python"

    def test_get_my_technologies_empty_list(self, client: TestClient, user_with_profile):
        """Test: Obtener lista vacía cuando no hay tecnologías"""
        # Arrange
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

        # Act
        response = client.get("/technologies/me", headers=headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_my_technologies_without_auth_fails(self, client: TestClient):
        """Test: Obtener tecnologías sin autenticación falla"""
        # Act
        response = client.get("/technologies/me")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # --- TESTS DE OBTENCIÓN POR ID ---

    def test_get_technology_by_id_success(self, client: TestClient, user_with_profile):
        """Test: Obtener tecnología por ID exitosamente"""
        # Arrange - Crear tecnología
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
        create_response = client.post(
            "/technologies", 
            json={"name": "PostgreSQL", "category": "databases"}, 
            headers=headers
        )
        tech_id = create_response.json()["id"]

        # Act
        response = client.get(f"/technologies/{tech_id}", headers=headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tech_id
        assert data["name"] == "PostgreSQL"
        assert data["category"] == "databases"

    def test_get_technology_nonexistent_id_fails(self, client: TestClient, user_with_profile):
        """Test: Obtener tecnología con ID inexistente falla"""
        # Arrange
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

        # Act
        response = client.get("/technologies/99999", headers=headers)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "no encontrad" in response.json()["detail"].lower()

    def test_get_technology_without_auth_fails(self, client: TestClient, user_with_profile):
        """Test: Obtener tecnología sin autenticación falla"""
        # Arrange - Crear tecnología
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
        create_response = client.post(
            "/technologies", 
            json={"name": "Redis", "category": "databases"}, 
            headers=headers
        )
        tech_id = create_response.json()["id"]

        # Act
        response = client.get(f"/technologies/{tech_id}")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # --- TESTS DE ACTUALIZACIÓN ---

    def test_update_technology_success(self, client: TestClient, user_with_profile):
        """Test: Actualizar tecnología exitosamente"""
        # Arrange - Crear tecnología
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
        create_response = client.post(
            "/technologies", 
            json={"name": "Node", "category": "backend"}, 
            headers=headers
        )
        tech_id = create_response.json()["id"]

        # Act - Actualizar
        update_data = {
            "name": "Node.js",
            "category": "backend",
            "icon_url": "https://icon.com/nodejs.svg"
        }
        response = client.put(f"/technologies/{tech_id}", json=update_data, headers=headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tech_id
        assert data["name"] == "Node.js"
        assert data["icon_url"] == "https://icon.com/nodejs.svg"

    def test_update_technology_partial_update(self, client: TestClient, user_with_profile):
        """Test: Actualización parcial solo modifica campos enviados"""
        # Arrange - Crear tecnología con icon_url
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
        create_response = client.post(
            "/technologies", 
            json={
                "name": "TypeScript",
                "category": "frontend",
                "icon_url": "https://icon.com/ts.svg"
            }, 
            headers=headers
        )
        tech_id = create_response.json()["id"]

        # Act - Actualizar solo el nombre
        update_data = {
            "name": "TypeScript 5.0"
        }
        response = client.put(f"/technologies/{tech_id}", json=update_data, headers=headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "TypeScript 5.0"
        assert data["category"] == "frontend"  # No cambió
        assert data["icon_url"] == "https://icon.com/ts.svg"  # No cambió

    def test_update_technology_nonexistent_id_fails(self, client: TestClient, user_with_profile):
        """Test: Actualizar tecnología inexistente falla"""
        # Arrange
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
        update_data = {"name": "Updated"}

        # Act
        response = client.put("/technologies/99999", json=update_data, headers=headers)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_technology_without_auth_fails(self, client: TestClient, user_with_profile):
        """Test: Actualizar tecnología sin autenticación falla"""
        # Arrange - Crear tecnología
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
        create_response = client.post(
            "/technologies", 
            json={"name": "MongoDB", "category": "databases"}, 
            headers=headers
        )
        tech_id = create_response.json()["id"]

        # Act
        update_data = {"name": "MongoDB Atlas"}
        response = client.put(f"/technologies/{tech_id}", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # --- TESTS DE ELIMINACIÓN ---

    def test_delete_technology_success(self, client: TestClient, user_with_profile):
        """Test: Eliminar tecnología exitosamente"""
        # Arrange - Crear tecnología
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
        create_response = client.post(
            "/technologies", 
            json={"name": "GraphQL", "category": "apis"}, 
            headers=headers
        )
        tech_id = create_response.json()["id"]

        # Act
        response = client.delete(f"/technologies/{tech_id}", headers=headers)

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify - No debe aparecer en el listado
        get_response = client.get("/technologies/me", headers=headers)
        techs = get_response.json()
        assert not any(tech["id"] == tech_id for tech in techs)

    def test_delete_technology_nonexistent_id_fails(self, client: TestClient, user_with_profile):
        """Test: Eliminar tecnología inexistente falla"""
        # Arrange
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

        # Act
        response = client.delete("/technologies/99999", headers=headers)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_technology_without_auth_fails(self, client: TestClient, user_with_profile):
        """Test: Eliminar tecnología sin autenticación falla"""
        # Arrange - Crear tecnología
        headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
        create_response = client.post(
            "/technologies", 
            json={"name": "REST", "category": "apis"}, 
            headers=headers
        )
        tech_id = create_response.json()["id"]

        # Act
        response = client.delete(f"/technologies/{tech_id}")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # --- TESTS MULTI-TENANT ---

    def test_technology_multi_tenant_isolation(
        self, 
        client: TestClient, 
        user_with_profile, 
        second_user_with_profile
    ):
        """Test: Usuarios solo pueden ver/modificar sus propias tecnologías"""
        # Arrange - Usuario 1 crea tecnología
        headers_user1 = {"Authorization": f"Bearer {user_with_profile['token']}"}
        create_response = client.post(
            "/technologies", 
            json={"name": "Kubernetes", "category": "cloud"}, 
            headers=headers_user1
        )
        tech_id_user1 = create_response.json()["id"]

        # Arrange - Usuario 2 crea tecnología
        headers_user2 = {"Authorization": f"Bearer {second_user_with_profile['token']}"}
        client.post(
            "/technologies", 
            json={"name": "AWS", "category": "cloud"}, 
            headers=headers_user2
        )

        # Act & Assert - Usuario 2 NO puede obtener tecnología de Usuario 1
        get_response = client.get(f"/technologies/{tech_id_user1}", headers=headers_user2)
        assert get_response.status_code == status.HTTP_403_FORBIDDEN

        # Act & Assert - Usuario 2 NO puede actualizar tecnología de Usuario 1
        update_response = client.put(
            f"/technologies/{tech_id_user1}", 
            json={"name": "Hacked"}, 
            headers=headers_user2
        )
        assert update_response.status_code == status.HTTP_403_FORBIDDEN

        # Act & Assert - Usuario 2 NO puede eliminar tecnología de Usuario 1
        delete_response = client.delete(f"/technologies/{tech_id_user1}", headers=headers_user2)
        assert delete_response.status_code == status.HTTP_403_FORBIDDEN

        # Act & Assert - Usuario 2 solo ve sus propias tecnologías
        list_response = client.get("/technologies/me", headers=headers_user2)
        techs = list_response.json()
        assert len(techs) == 1
        assert techs[0]["name"] == "AWS"

    # --- TEST DE FLUJO COMPLETO ---

    def test_complete_technology_flow(self, client: TestClient):
        """Test: Flujo completo - Registro, Login, Crear Perfil, CRUD Tecnologías"""
        # Step 1: Registro
        register_data = {
            "username": "flowtech",
            "email": "flowtech@example.com",
            "password": "password123"
        }
        register_response = client.post("/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Step 2: Login
        login_data = {
            "username": "flowtech@example.com",
            "password": "password123"
        }
        login_response = client.post("/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: Crear perfil (prerequisito)
        profile_data = {
            "name": "Flow",
            "last_name": "Tech",
            "current_title": "DevOps Engineer"
        }
        profile_response = client.post("/profile", json=profile_data, headers=headers)
        assert profile_response.status_code == status.HTTP_201_CREATED

        # Step 4: Crear tecnología
        tech_data = {
            "name": "Jenkins",
            "category": "dev_tools",
            "icon_url": "https://icon.com/jenkins.svg"
        }
        create_response = client.post("/technologies", json=tech_data, headers=headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        tech_id = create_response.json()["id"]

        # Step 5: Obtener tecnología
        get_response = client.get(f"/technologies/{tech_id}", headers=headers)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["name"] == "Jenkins"

        # Step 6: Listar tecnologías
        list_response = client.get("/technologies/me", headers=headers)
        assert list_response.status_code == status.HTTP_200_OK
        assert len(list_response.json()) == 1

        # Step 7: Actualizar tecnología
        update_data = {"name": "Jenkins CI/CD"}
        update_response = client.put(f"/technologies/{tech_id}", json=update_data, headers=headers)
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["name"] == "Jenkins CI/CD"

        # Step 8: Eliminar tecnología
        delete_response = client.delete(f"/technologies/{tech_id}", headers=headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Step 9: Verificar eliminación
        list_after_delete = client.get("/technologies/me", headers=headers)
        assert len(list_after_delete.json()) == 0
