"""
Tests de Integración - Client Flow

Valida el flujo completo de operaciones CRUD de clientes:
- Creación con autenticación (ADMIN only) y multi-tenant
- Listado de clientes propios
- Obtención por ID con validación de ownership
- Actualización con ownership validation (ADMIN only)
- Eliminación (soft delete) con ownership validation (ADMIN only)
- Aislamiento multi-tenant entre usuarios
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestClientFlow:
    """Suite de tests para el flujo completo de Client"""

    # --- FIXTURES HELPERS ---
    
    @pytest.fixture
    def authenticated_user(self, client: TestClient):
        """Usuario registrado y autenticado"""
        user_data = {
            "username": "client_user",
            "email": "client@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "username": "client@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        return {"email": "client@example.com", "token": token}

    @pytest.fixture
    def user_with_profile(self, client: TestClient, authenticated_user):
        """Usuario con perfil creado (requerido para clientes)"""
        profile_data = {
            "name": "Client",
            "last_name": "Manager",
            "current_title": "Business Developer"
        }
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        client.post("/profile", json=profile_data, headers=headers)
        return authenticated_user

    @pytest.fixture
    def second_user_with_profile(self, client: TestClient):
        """Segundo usuario para pruebas multi-tenant"""
        user_data = {
            "username": "client_user2",
            "email": "client2@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "username": "client2@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        
        # Crear perfil
        profile_data = {
            "name": "Client2",
            "last_name": "Manager2",
            "current_title": "Sales Director"
        }
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/profile", json=profile_data, headers=headers)
        
        return {"email": "client2@example.com", "token": token}

    # --- TEST CREATE CLIENT ---

    def test_create_client_success(self, client: TestClient, user_with_profile: dict):
        """Test crear cliente exitosamente."""
        token = user_with_profile["token"]
        
        response = client.post(
            "/clients",
            json={
                "name": "John Doe",
                "company": "Acme Corporation",
                "feedback": "Excellent work on the project!",
                "client_photo_url": "https://example.com/photo.jpg",
                "project_link": "https://example.com/project"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["company"] == "Acme Corporation"
        assert data["feedback"] == "Excellent work on the project!"
        assert data["client_photo_url"] == "https://example.com/photo.jpg"
        assert data["project_link"] == "https://example.com/project"
        assert "id" in data
        assert "profile_id" in data

    def test_create_client_minimal_fields(self, client: TestClient, user_with_profile: dict):
        """Test crear cliente solo con campos requeridos."""
        token = user_with_profile["token"]
        
        response = client.post(
            "/clients",
            json={"name": "Jane Smith"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Jane Smith"
        assert data["company"] is None
        assert data["feedback"] is None
        assert data["client_photo_url"] is None
        assert data["project_link"] is None

    def test_create_client_missing_required_fields(self, client: TestClient, user_with_profile: dict):
        """Test crear cliente sin campos requeridos."""
        token = user_with_profile["token"]
        
        response = client.post(
            "/clients",
            json={"company": "Test Company"},  # Falta name
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422

    def test_create_client_invalid_name_too_short(self, client: TestClient, user_with_profile: dict):
        """Test crear cliente con name muy corto."""
        token = user_with_profile["token"]
        
        response = client.post(
            "/clients",
            json={"name": "A"},  # Solo 1 caracter, min_length=2
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422

    def test_create_client_without_profile(self, client: TestClient, authenticated_user: dict):
        """Test crear cliente sin tener perfil."""
        token = authenticated_user["token"]
        
        response = client.post(
            "/clients",
            json={"name": "Test Client"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400

    def test_create_client_unauthorized(self, client: TestClient):
        """Test crear cliente sin autenticación."""
        response = client.post(
            "/clients",
            json={"name": "Test Client"}
        )
        
        assert response.status_code == 401

    # --- TEST GET MY CLIENTS ---

    def test_get_my_clients_success(self, client: TestClient, user_with_profile: dict):
        """Test obtener mis clientes exitosamente."""
        token = user_with_profile["token"]
        
        # Crear algunos clientes
        client.post(
            "/clients",
            json={
                "name": "John Doe",
                "company": "Acme Corp",
                "feedback": "Great work!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        client.post(
            "/clients",
            json={
                "name": "Jane Smith",
                "company": "Beta Inc",
                "feedback": "Excellent service!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Obtener lista
        response = client.get(
            "/clients/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = [c["name"] for c in data]
        assert "John Doe" in names
        assert "Jane Smith" in names

    def test_get_my_clients_empty(self, client: TestClient, user_with_profile: dict):
        """Test obtener mis clientes cuando no hay ninguno."""
        token = user_with_profile["token"]
        
        response = client.get(
            "/clients/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_my_clients_unauthorized(self, client: TestClient):
        """Test obtener mis clientes sin autenticación."""
        response = client.get("/clients/me")
        
        assert response.status_code == 401

    # --- TEST GET CLIENT BY ID ---

    def test_get_client_by_id_success(self, client: TestClient, user_with_profile: dict):
        """Test obtener un cliente por ID exitosamente."""
        token = user_with_profile["token"]
        
        # Crear cliente
        create_response = client.post(
            "/clients",
            json={
                "name": "John Doe",
                "company": "Acme Corp",
                "feedback": "Great work!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        client_id = create_response.json()["id"]
        
        # Obtener por ID
        response = client.get(
            f"/clients/{client_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == client_id
        assert data["name"] == "John Doe"

    def test_get_client_by_id_not_found(self, client: TestClient, user_with_profile: dict):
        """Test obtener un cliente que no existe."""
        token = user_with_profile["token"]
        
        response = client.get(
            "/clients/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404

    def test_get_client_by_id_unauthorized_access(
        self,
        client: TestClient,
        user_with_profile: dict,
        second_user_with_profile: dict
    ):
        """Test que un usuario no puede acceder a cliente de otro usuario."""
        token1 = user_with_profile["token"]
        token2 = second_user_with_profile["token"]
        
        # Usuario 1 crea un cliente
        create_response = client.post(
            "/clients",
            json={"name": "John Doe", "company": "Company A"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        client_id = create_response.json()["id"]
        
        # Usuario 2 intenta acceder al cliente de Usuario 1
        response = client.get(
            f"/clients/{client_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 403

    # --- TEST UPDATE CLIENT ---

    def test_update_client_success(self, client: TestClient, user_with_profile: dict):
        """Test actualizar un cliente exitosamente."""
        token = user_with_profile["token"]
        
        # Crear cliente
        create_response = client.post(
            "/clients",
            json={
                "name": "John Doe",
                "company": "Acme Corp",
                "feedback": "Great work!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        client_id = create_response.json()["id"]
        
        # Actualizar
        response = client.put(
            f"/clients/{client_id}",
            json={
                "name": "John Smith",
                "company": "Beta Corp",
                "feedback": "Excellent work!",
                "client_photo_url": "https://example.com/new-photo.jpg"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == client_id
        assert data["name"] == "John Smith"
        assert data["company"] == "Beta Corp"
        assert data["feedback"] == "Excellent work!"
        assert data["client_photo_url"] == "https://example.com/new-photo.jpg"

    def test_update_client_partial(self, client: TestClient, user_with_profile: dict):
        """Test actualizar un cliente parcialmente."""
        token = user_with_profile["token"]
        
        # Crear cliente
        create_response = client.post(
            "/clients",
            json={
                "name": "John Doe",
                "company": "Acme Corp",
                "feedback": "Great!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        client_id = create_response.json()["id"]
        
        # Actualizar solo el feedback
        response = client.put(
            f"/clients/{client_id}",
            json={"feedback": "Outstanding work!"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["feedback"] == "Outstanding work!"
        assert data["name"] == "John Doe"  # Sin cambios
        assert data["company"] == "Acme Corp"  # Sin cambios

    def test_update_client_not_found(self, client: TestClient, user_with_profile: dict):
        """Test actualizar un cliente que no existe."""
        token = user_with_profile["token"]
        
        response = client.put(
            "/clients/99999",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404

    def test_update_client_unauthorized_access(
        self,
        client: TestClient,
        user_with_profile: dict,
        second_user_with_profile: dict
    ):
        """Test que un usuario no puede actualizar cliente de otro usuario."""
        token1 = user_with_profile["token"]
        token2 = second_user_with_profile["token"]
        
        # Usuario 1 crea un cliente
        create_response = client.post(
            "/clients",
            json={"name": "John Doe"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        client_id = create_response.json()["id"]
        
        # Usuario 2 intenta actualizar el cliente de Usuario 1
        response = client.put(
            f"/clients/{client_id}",
            json={"name": "Hacked Name"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 403

    def test_update_client_invalid_name_too_short(self, client: TestClient, user_with_profile: dict):
        """Test actualizar con name muy corto."""
        token = user_with_profile["token"]
        
        # Crear cliente
        create_response = client.post(
            "/clients",
            json={"name": "John Doe"},
            headers={"Authorization": f"Bearer {token}"}
        )
        client_id = create_response.json()["id"]
        
        # Intentar actualizar con name inválido
        response = client.put(
            f"/clients/{client_id}",
            json={"name": "A"},  # Solo 1 caracter
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422

    # --- TEST DELETE CLIENT ---

    def test_delete_client_success(self, client: TestClient, user_with_profile: dict):
        """Test eliminar un cliente exitosamente."""
        token = user_with_profile["token"]
        
        # Crear cliente
        create_response = client.post(
            "/clients",
            json={"name": "John Doe"},
            headers={"Authorization": f"Bearer {token}"}
        )
        client_id = create_response.json()["id"]
        
        # Eliminar
        response = client.delete(
            f"/clients/{client_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Verificar que ya no existe
        get_response = client.get(
            f"/clients/{client_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 404

    def test_delete_client_not_found(self, client: TestClient, user_with_profile: dict):
        """Test eliminar un cliente que no existe."""
        token = user_with_profile["token"]
        
        response = client.delete(
            "/clients/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404

    def test_delete_client_unauthorized_access(
        self,
        client: TestClient,
        user_with_profile: dict,
        second_user_with_profile: dict
    ):
        """Test que un usuario no puede eliminar cliente de otro usuario."""
        token1 = user_with_profile["token"]
        token2 = second_user_with_profile["token"]
        
        # Usuario 1 crea un cliente
        create_response = client.post(
            "/clients",
            json={"name": "John Doe"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        client_id = create_response.json()["id"]
        
        # Usuario 2 intenta eliminar el cliente de Usuario 1
        response = client.delete(
            f"/clients/{client_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 403

    # --- TEST MULTI-TENANT ISOLATION ---

    def test_multi_tenant_isolation(
        self,
        client: TestClient,
        user_with_profile: dict,
        second_user_with_profile: dict
    ):
        """Test que cada usuario solo ve sus propios clientes."""
        token1 = user_with_profile["token"]
        token2 = second_user_with_profile["token"]
        
        # Usuario 1 crea clientes
        client.post(
            "/clients",
            json={"name": "Client A", "company": "Company A"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        client.post(
            "/clients",
            json={"name": "Client B", "company": "Company B"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        # Usuario 2 crea clientes
        client.post(
            "/clients",
            json={"name": "Client C", "company": "Company C"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        # Usuario 1 obtiene sus clientes
        response1 = client.get(
            "/clients/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        data1 = response1.json()
        assert len(data1) == 2
        
        # Usuario 2 obtiene sus clientes
        response2 = client.get(
            "/clients/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        data2 = response2.json()
        assert len(data2) == 1

    # --- TEST COMPLETE FLOW ---

    def test_complete_client_flow(self, client: TestClient, user_with_profile: dict):
        """Test flujo completo: crear, listar, obtener, actualizar y eliminar clientes."""
        token = user_with_profile["token"]
        
        # 1. Crear múltiples clientes
        client1_response = client.post(
            "/clients",
            json={
                "name": "John Doe",
                "company": "Acme Corp",
                "feedback": "Great work!",
                "client_photo_url": "https://example.com/john.jpg"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert client1_response.status_code == 201
        client1_id = client1_response.json()["id"]
        
        client2_response = client.post(
            "/clients",
            json={
                "name": "Jane Smith",
                "company": "Beta Inc",
                "feedback": "Excellent service!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert client2_response.status_code == 201
        client2_id = client2_response.json()["id"]
        
        # 2. Listar todos los clientes
        list_response = client.get(
            "/clients/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200
        assert len(list_response.json()) == 2
        
        # 3. Obtener un cliente específico
        get_response = client.get(
            f"/clients/{client1_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "John Doe"
        
        # 4. Actualizar un cliente
        update_response = client.put(
            f"/clients/{client1_id}",
            json={
                "feedback": "Outstanding work!",
                "project_link": "https://example.com/project"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["feedback"] == "Outstanding work!"
        assert update_response.json()["project_link"] == "https://example.com/project"
        
        # 5. Eliminar un cliente
        delete_response = client.delete(
            f"/clients/{client2_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_response.status_code == 204
        
        # 6. Verificar que solo queda uno
        final_list = client.get(
            "/clients/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert len(final_list.json()) == 1
        assert final_list.json()[0]["id"] == client1_id
