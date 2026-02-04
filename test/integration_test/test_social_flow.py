"""
Tests de Integración - Social Flow

Valida el flujo completo de operaciones CRUD de social links:
- Creación con autenticación (ADMIN only) y multi-tenant
- Listado de social links propios
- Obtención por ID con validación de ownership
- Actualización con ownership validation (ADMIN only)
- Eliminación (soft delete) con ownership validation (ADMIN only)
- Aislamiento multi-tenant entre usuarios
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestSocialFlow:
    """Suite de tests para el flujo completo de Social"""

    # --- FIXTURES HELPERS ---
    
    @pytest.fixture
    def authenticated_user(self, client: TestClient):
        """Usuario registrado y autenticado"""
        user_data = {
            "username": "social_user",
            "email": "social@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "username": "social@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        return {"email": "social@example.com", "token": token}

    @pytest.fixture
    def user_with_profile(self, client: TestClient, authenticated_user):
        """Usuario con perfil creado (requerido para social links)"""
        profile_data = {
            "name": "Social",
            "last_name": "User",
            "current_title": "Software Developer"
        }
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        client.post("/profile", json=profile_data, headers=headers)
        return authenticated_user

    @pytest.fixture
    def second_user_with_profile(self, client: TestClient):
        """Segundo usuario para pruebas multi-tenant"""
        user_data = {
            "username": "social_user2",
            "email": "social2@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "username": "social2@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        
        # Crear perfil
        profile_data = {
            "name": "Social2",
            "last_name": "User2",
            "current_title": "Product Manager"
        }
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/profile", json=profile_data, headers=headers)
        
        return {"email": "social2@example.com", "token": token}

    # --- TEST CREATE SOCIAL ---

    def test_create_social_success(self, client: TestClient, user_with_profile: dict):
        """Test crear social link exitosamente."""
        token = user_with_profile["token"]
        
        response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe",
                "icon_name": "github",
                "order": 1
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["platform"] == "GitHub"
        assert data["url"] == "https://github.com/johndoe"
        assert data["icon_name"] == "github"
        assert data["order"] == 1
        assert "id" in data
        assert "profile_id" in data

    def test_create_social_missing_required_fields(self, client: TestClient, user_with_profile: dict):
        """Test crear social link sin campos requeridos."""
        token = user_with_profile["token"]
        
        response = client.post(
            "/social",
            json={"platform": "GitHub"},  # Falta url
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422

    def test_create_social_invalid_platform_too_short(self, client: TestClient, user_with_profile: dict):
        """Test crear social link con platform muy corto."""
        token = user_with_profile["token"]
        
        response = client.post(
            "/social",
            json={
                "platform": "X",  # Solo 1 caracter, min_length=2
                "url": "https://x.com/johndoe"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422

    def test_create_social_without_profile(self, client: TestClient, authenticated_user: dict):
        """Test crear social link sin tener perfil."""
        token = authenticated_user["token"]
        
        response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400

    def test_create_social_unauthorized(self, client: TestClient):
        """Test crear social link sin autenticación."""
        response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe"
            }
        )
        
        assert response.status_code == 401

    # --- TEST GET MY SOCIALS ---

    def test_get_my_socials_success(self, client: TestClient, user_with_profile: dict):
        """Test obtener mis social links exitosamente."""
        token = user_with_profile["token"]
        
        # Crear algunos social links
        client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe",
                "icon_name": "github",
                "order": 1
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        client.post(
            "/social",
            json={
                "platform": "LinkedIn",
                "url": "https://linkedin.com/in/johndoe",
                "icon_name": "linkedin",
                "order": 2
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Obtener lista
        response = client.get(
            "/social/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["platform"] == "GitHub"
        assert data[1]["platform"] == "LinkedIn"

    def test_get_my_socials_empty(self, client: TestClient, user_with_profile: dict):
        """Test obtener mis social links cuando no hay ninguno."""
        token = user_with_profile["token"]
        
        response = client.get(
            "/social/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_my_socials_unauthorized(self, client: TestClient):
        """Test obtener mis social links sin autenticación."""
        response = client.get("/social/me")
        
        assert response.status_code == 401

    # --- TEST GET SOCIAL BY ID ---

    def test_get_social_by_id_success(self, client: TestClient, user_with_profile: dict):
        """Test obtener un social link por ID exitosamente."""
        token = user_with_profile["token"]
        
        # Crear social link
        create_response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe",
                "icon_name": "github",
                "order": 1
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        social_id = create_response.json()["id"]
        
        # Obtener por ID
        response = client.get(
            f"/social/{social_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == social_id
        assert data["platform"] == "GitHub"

    def test_get_social_by_id_not_found(self, client: TestClient, user_with_profile: dict):
        """Test obtener un social link que no existe."""
        token = user_with_profile["token"]
        
        response = client.get(
            "/social/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404

    def test_get_social_by_id_unauthorized_access(
        self,
        client: TestClient,
        user_with_profile: dict,
        second_user_with_profile: dict
    ):
        """Test que un usuario no puede acceder a social link de otro usuario."""
        token1 = user_with_profile["token"]
        token2 = second_user_with_profile["token"]
        
        # Usuario 1 crea un social link
        create_response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/user1"
            },
            headers={"Authorization": f"Bearer {token1}"}
        )
        social_id = create_response.json()["id"]
        
        # Usuario 2 intenta acceder al social link de Usuario 1
        response = client.get(
            f"/social/{social_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 403

    # --- TEST UPDATE SOCIAL ---

    def test_update_social_success(self, client: TestClient, user_with_profile: dict):
        """Test actualizar un social link exitosamente."""
        token = user_with_profile["token"]
        
        # Crear social link
        create_response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe",
                "icon_name": "github",
                "order": 1
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        social_id = create_response.json()["id"]
        
        # Actualizar
        response = client.put(
            f"/social/{social_id}",
            json={
                "platform": "GitLab",
                "url": "https://gitlab.com/johndoe",
                "icon_name": "gitlab",
                "order": 2
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == social_id
        assert data["platform"] == "GitLab"
        assert data["url"] == "https://gitlab.com/johndoe"
        assert data["icon_name"] == "gitlab"
        assert data["order"] == 2

    def test_update_social_partial(self, client: TestClient, user_with_profile: dict):
        """Test actualizar un social link parcialmente."""
        token = user_with_profile["token"]
        
        # Crear social link
        create_response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe",
                "icon_name": "github",
                "order": 1
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        social_id = create_response.json()["id"]
        
        # Actualizar solo la URL
        response = client.put(
            f"/social/{social_id}",
            json={"url": "https://github.com/johndoe-updated"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://github.com/johndoe-updated"
        assert data["platform"] == "GitHub"  # Sin cambios
        assert data["icon_name"] == "github"  # Sin cambios

    def test_update_social_not_found(self, client: TestClient, user_with_profile: dict):
        """Test actualizar un social link que no existe."""
        token = user_with_profile["token"]
        
        response = client.put(
            "/social/99999",
            json={"platform": "Updated"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404

    def test_update_social_unauthorized_access(
        self,
        client: TestClient,
        user_with_profile: dict,
        second_user_with_profile: dict
    ):
        """Test que un usuario no puede actualizar social link de otro usuario."""
        token1 = user_with_profile["token"]
        token2 = second_user_with_profile["token"]
        
        # Usuario 1 crea un social link
        create_response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/user1"
            },
            headers={"Authorization": f"Bearer {token1}"}
        )
        social_id = create_response.json()["id"]
        
        # Usuario 2 intenta actualizar el social link de Usuario 1
        response = client.put(
            f"/social/{social_id}",
            json={"platform": "Hacked"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 403

    def test_update_social_invalid_platform_too_short(self, client: TestClient, user_with_profile: dict):
        """Test actualizar con platform muy corto."""
        token = user_with_profile["token"]
        
        # Crear social link
        create_response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        social_id = create_response.json()["id"]
        
        # Intentar actualizar con platform inválido
        response = client.put(
            f"/social/{social_id}",
            json={"platform": "X"},  # Solo 1 caracter
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422

    # --- TEST DELETE SOCIAL ---

    def test_delete_social_success(self, client: TestClient, user_with_profile: dict):
        """Test eliminar un social link exitosamente."""
        token = user_with_profile["token"]
        
        # Crear social link
        create_response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        social_id = create_response.json()["id"]
        
        # Eliminar
        response = client.delete(
            f"/social/{social_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Verificar que ya no existe
        get_response = client.get(
            f"/social/{social_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 404

    def test_delete_social_not_found(self, client: TestClient, user_with_profile: dict):
        """Test eliminar un social link que no existe."""
        token = user_with_profile["token"]
        
        response = client.delete(
            "/social/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404

    def test_delete_social_unauthorized_access(
        self,
        client: TestClient,
        user_with_profile: dict,
        second_user_with_profile: dict
    ):
        """Test que un usuario no puede eliminar social link de otro usuario."""
        token1 = user_with_profile["token"]
        token2 = second_user_with_profile["token"]
        
        # Usuario 1 crea un social link
        create_response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/user1"
            },
            headers={"Authorization": f"Bearer {token1}"}
        )
        social_id = create_response.json()["id"]
        
        # Usuario 2 intenta eliminar el social link de Usuario 1
        response = client.delete(
            f"/social/{social_id}",
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
        """Test que cada usuario solo ve sus propios social links."""
        token1 = user_with_profile["token"]
        token2 = second_user_with_profile["token"]
        
        # Usuario 1 crea social links
        client.post(
            "/social",
            json={"platform": "GitHub", "url": "https://github.com/user1"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        client.post(
            "/social",
            json={"platform": "LinkedIn", "url": "https://linkedin.com/in/user1"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        # Usuario 2 crea social links
        client.post(
            "/social",
            json={"platform": "Twitter", "url": "https://twitter.com/user2"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        # Usuario 1 obtiene sus social links
        response1 = client.get(
            "/social/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        data1 = response1.json()
        assert len(data1) == 2
        
        # Usuario 2 obtiene sus social links
        response2 = client.get(
            "/social/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        data2 = response2.json()
        assert len(data2) == 1

    # --- TEST COMPLETE FLOW ---

    def test_complete_social_flow(self, client: TestClient, user_with_profile: dict):
        """Test flujo completo: crear, listar, obtener, actualizar y eliminar social links."""
        token = user_with_profile["token"]
        
        # 1. Crear múltiples social links
        github_response = client.post(
            "/social",
            json={
                "platform": "GitHub",
                "url": "https://github.com/johndoe",
                "icon_name": "github",
                "order": 1
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert github_response.status_code == 201
        github_id = github_response.json()["id"]
        
        linkedin_response = client.post(
            "/social",
            json={
                "platform": "LinkedIn",
                "url": "https://linkedin.com/in/johndoe",
                "icon_name": "linkedin",
                "order": 2
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert linkedin_response.status_code == 201
        linkedin_id = linkedin_response.json()["id"]
        
        # 2. Listar todos los social links
        list_response = client.get(
            "/social/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200
        assert len(list_response.json()) == 2
        
        # 3. Obtener un social link específico
        get_response = client.get(
            f"/social/{github_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
        assert get_response.json()["platform"] == "GitHub"
        
        # 4. Actualizar un social link
        update_response = client.put(
            f"/social/{github_id}",
            json={
                "url": "https://github.com/johndoe-updated",
                "order": 3
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["url"] == "https://github.com/johndoe-updated"
        assert update_response.json()["order"] == 3
        
        # 5. Eliminar un social link
        delete_response = client.delete(
            f"/social/{linkedin_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_response.status_code == 204
        
        # 6. Verificar que solo queda uno
        final_list = client.get(
            "/social/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert len(final_list.json()) == 1
        assert final_list.json()[0]["id"] == github_id
