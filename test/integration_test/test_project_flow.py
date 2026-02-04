"""
Tests de Integración - Project Flow

Cobertura:
- Creación con/sin perfil, con/sin auth, categoría inválida
- Listado de proyectos propios y destacados
- Obtención por ID con validación de ownership
- Actualización parcial y con reemplazo de tecnologías/previews
- Eliminación (soft delete)
- Aislamiento multi-tenant
- Flujo completo de principio a fin
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestProjectFlow:
	"""Suite de tests para el flujo completo de Project"""

	# --- FIXTURES HELPERS ---

	@pytest.fixture
	def authenticated_user(self, client: TestClient):
		"""Usuario registrado y autenticado"""
		user_data = {
			"username": "project_user",
			"email": "project@example.com",
			"password": "password123"
		}
		client.post("/auth/register", json=user_data)

		login_data = {
			"username": "project@example.com",
			"password": "password123"
		}
		response = client.post("/auth/login", data=login_data)
		token = response.json()["access_token"]
		return {"email": "project@example.com", "token": token}

	@pytest.fixture
	def user_with_profile(self, client: TestClient, authenticated_user):
		"""Usuario con perfil creado (requerido para proyectos)"""
		profile_data = {
			"name": "Project",
			"last_name": "Owner",
			"current_title": "Full Stack Developer"
		}
		headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
		client.post("/profile", json=profile_data, headers=headers)
		return authenticated_user

	@pytest.fixture
	def second_user_with_profile(self, client: TestClient):
		"""Segundo usuario para pruebas multi-tenant"""
		user_data = {
			"username": "project_user2",
			"email": "project2@example.com",
			"password": "password123"
		}
		client.post("/auth/register", json=user_data)

		login_data = {
			"username": "project2@example.com",
			"password": "password123"
		}
		response = client.post("/auth/login", data=login_data)
		token = response.json()["access_token"]

		profile_data = {
			"name": "Project2",
			"last_name": "Owner2",
			"current_title": "Backend Developer"
		}
		headers = {"Authorization": f"Bearer {token}"}
		client.post("/profile", json=profile_data, headers=headers)

		return {"email": "project2@example.com", "token": token}

	def _create_technologies(self, client: TestClient, token: str):
		headers = {"Authorization": f"Bearer {token}"}
		tech1 = client.post(
			"/technologies",
			json={"name": "Python", "category": "backend"},
			headers=headers
		).json()["id"]
		tech2 = client.post(
			"/technologies",
			json={"name": "React", "category": "frontend"},
			headers=headers
		).json()["id"]
		return tech1, tech2

	# --- TESTS DE CREACIÓN ---

	def test_create_project_success_minimal(self, client: TestClient, user_with_profile):
		"""Test: Crear proyecto con datos mínimos"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		project_data = {
			"title": "Mi Proyecto",
			"category": "fullstack"
		}

		response = client.post("/projects", json=project_data, headers=headers)

		assert response.status_code == status.HTTP_201_CREATED
		data = response.json()
		assert data["title"] == "Mi Proyecto"
		assert data["category"] == "fullstack"
		assert data["featured"] is False
		assert data["technology_ids"] == []
		assert data["previews"] == []
		assert "id" in data
		assert "profile_id" in data

	def test_create_project_with_techs_and_previews(self, client: TestClient, user_with_profile):
		"""Test: Crear proyecto con tecnologías y previews"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		tech1, tech2 = self._create_technologies(client, user_with_profile["token"])

		project_data = {
			"title": "Proyecto Completo",
			"category": "backend",
			"description": "API con FastAPI",
			"featured": True,
			"technology_ids": [tech1, tech2],
			"previews": [
				{"image_url": "https://img.com/2.png", "caption": "Home", "order": 2},
				{"image_url": "https://img.com/1.png", "caption": "Login", "order": 1}
			]
		}

		response = client.post("/projects", json=project_data, headers=headers)

		assert response.status_code == status.HTTP_201_CREATED
		data = response.json()
		assert data["title"] == "Proyecto Completo"
		assert data["featured"] is True
		assert set(data["technology_ids"]) == {tech1, tech2}
		assert len(data["previews"]) == 2
		assert data["previews"][0]["order"] == 1
		assert data["previews"][1]["order"] == 2

	def test_create_project_without_profile_fails(self, client: TestClient, authenticated_user):
		"""Test: Crear proyecto sin perfil falla"""
		headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
		project_data = {
			"title": "Proyecto Sin Perfil",
			"category": "frontend"
		}

		response = client.post("/projects", json=project_data, headers=headers)

		assert response.status_code == status.HTTP_400_BAD_REQUEST
		assert "perfil" in response.json()["detail"].lower()

	def test_create_project_without_auth_fails(self, client: TestClient):
		"""Test: Crear proyecto sin autenticación falla"""
		project_data = {
			"title": "Proyecto Sin Auth",
			"category": "backend"
		}

		response = client.post("/projects", json=project_data)

		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	def test_create_project_invalid_category_fails(self, client: TestClient, user_with_profile):
		"""Test: Crear proyecto con categoría inválida falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		project_data = {
			"title": "Proyecto",
			"category": "invalid"
		}

		response = client.post("/projects", json=project_data, headers=headers)

		assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

	# --- TESTS DE LISTADO ---

	def test_get_my_projects_success(self, client: TestClient, user_with_profile):
		"""Test: Obtener lista de proyectos (featured primero)"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

		client.post(
			"/projects",
			json={"title": "Normal", "category": "backend", "featured": False},
			headers=headers
		)
		client.post(
			"/projects",
			json={"title": "Destacado", "category": "backend", "featured": True},
			headers=headers
		)

		response = client.get("/projects/me", headers=headers)

		assert response.status_code == status.HTTP_200_OK
		data = response.json()
		assert len(data) == 2
		assert data[0]["featured"] is True

	def test_get_my_projects_empty_list(self, client: TestClient, user_with_profile):
		"""Test: Obtener lista vacía cuando no hay proyectos"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

		response = client.get("/projects/me", headers=headers)

		assert response.status_code == status.HTTP_200_OK
		assert response.json() == []

	def test_get_my_projects_without_auth_fails(self, client: TestClient):
		"""Test: Obtener proyectos sin autenticación falla"""
		response = client.get("/projects/me")
		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	def test_get_my_featured_projects_success(self, client: TestClient, user_with_profile):
		"""Test: Obtener solo proyectos destacados"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

		client.post(
			"/projects",
			json={"title": "Normal", "category": "backend", "featured": False},
			headers=headers
		)
		client.post(
			"/projects",
			json={"title": "Destacado", "category": "backend", "featured": True},
			headers=headers
		)

		response = client.get("/projects/featured", headers=headers)

		assert response.status_code == status.HTTP_200_OK
		data = response.json()
		assert len(data) == 1
		assert data[0]["featured"] is True

	# --- TESTS DE OBTENCIÓN POR ID ---

	def test_get_project_by_id_success(self, client: TestClient, user_with_profile):
		"""Test: Obtener proyecto por ID exitosamente"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/projects",
			json={"title": "API", "category": "backend"},
			headers=headers
		)
		project_id = create_response.json()["id"]

		response = client.get(f"/projects/{project_id}", headers=headers)

		assert response.status_code == status.HTTP_200_OK
		data = response.json()
		assert data["id"] == project_id
		assert data["title"] == "API"

	def test_get_project_nonexistent_id_fails(self, client: TestClient, user_with_profile):
		"""Test: Obtener proyecto inexistente falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		response = client.get("/projects/99999", headers=headers)

		assert response.status_code == status.HTTP_404_NOT_FOUND

	def test_get_project_without_auth_fails(self, client: TestClient, user_with_profile):
		"""Test: Obtener proyecto sin autenticación falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/projects",
			json={"title": "Web", "category": "frontend"},
			headers=headers
		)
		project_id = create_response.json()["id"]

		response = client.get(f"/projects/{project_id}")

		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	# --- TESTS DE ACTUALIZACIÓN ---

	def test_update_project_success(self, client: TestClient, user_with_profile):
		"""Test: Actualizar proyecto exitosamente"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		tech1, tech2 = self._create_technologies(client, user_with_profile["token"])

		create_response = client.post(
			"/projects",
			json={
				"title": "Original",
				"category": "backend",
				"technology_ids": [tech1],
				"previews": [
					{"image_url": "https://img.com/old.png", "caption": "Old", "order": 1}
				]
			},
			headers=headers
		)
		project_id = create_response.json()["id"]

		update_data = {
			"title": "Actualizado",
			"featured": True,
			"technology_ids": [tech2],
			"previews": [
				{"image_url": "https://img.com/new.png", "caption": "New", "order": 1}
			]
		}

		response = client.put(f"/projects/{project_id}", json=update_data, headers=headers)

		assert response.status_code == status.HTTP_200_OK
		data = response.json()
		assert data["title"] == "Actualizado"
		assert data["featured"] is True
		assert data["technology_ids"] == [tech2]
		assert len(data["previews"]) == 1
		assert data["previews"][0]["caption"] == "New"

	def test_update_project_partial_update(self, client: TestClient, user_with_profile):
		"""Test: Actualización parcial mantiene campos no enviados"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/projects",
			json={"title": "Keep", "category": "frontend", "description": "Old"},
			headers=headers
		)
		project_id = create_response.json()["id"]

		response = client.put(
			f"/projects/{project_id}",
			json={"description": "New"},
			headers=headers
		)

		assert response.status_code == status.HTTP_200_OK
		data = response.json()
		assert data["title"] == "Keep"
		assert data["description"] == "New"
		assert data["category"] == "frontend"

	def test_update_project_nonexistent_id_fails(self, client: TestClient, user_with_profile):
		"""Test: Actualizar proyecto inexistente falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		response = client.put("/projects/99999", json={"title": "Valid"}, headers=headers)

		assert response.status_code == status.HTTP_404_NOT_FOUND

	def test_update_project_without_auth_fails(self, client: TestClient, user_with_profile):
		"""Test: Actualizar proyecto sin autenticación falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/projects",
			json={"title": "Auth", "category": "backend"},
			headers=headers
		)
		project_id = create_response.json()["id"]

		response = client.put(f"/projects/{project_id}", json={"title": "No"})

		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	# --- TESTS DE ELIMINACIÓN ---

	def test_delete_project_success(self, client: TestClient, user_with_profile):
		"""Test: Eliminar proyecto exitosamente"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/projects",
			json={"title": "Delete", "category": "backend"},
			headers=headers
		)
		project_id = create_response.json()["id"]

		response = client.delete(f"/projects/{project_id}", headers=headers)

		assert response.status_code == status.HTTP_204_NO_CONTENT

		list_response = client.get("/projects/me", headers=headers)
		assert list_response.status_code == status.HTTP_200_OK
		assert list_response.json() == []

	def test_delete_project_nonexistent_id_fails(self, client: TestClient, user_with_profile):
		"""Test: Eliminar proyecto inexistente falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		response = client.delete("/projects/99999", headers=headers)

		assert response.status_code == status.HTTP_404_NOT_FOUND

	def test_delete_project_without_auth_fails(self, client: TestClient, user_with_profile):
		"""Test: Eliminar proyecto sin autenticación falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/projects",
			json={"title": "NoAuth", "category": "backend"},
			headers=headers
		)
		project_id = create_response.json()["id"]

		response = client.delete(f"/projects/{project_id}")

		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	# --- TESTS MULTI-TENANT ---

	def test_project_multi_tenant_isolation(
		self,
		client: TestClient,
		user_with_profile,
		second_user_with_profile
	):
		"""Test: Usuarios solo pueden ver/modificar sus propios proyectos"""
		headers_user1 = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/projects",
			json={"title": "User1", "category": "backend"},
			headers=headers_user1
		)
		project_id_user1 = create_response.json()["id"]

		headers_user2 = {"Authorization": f"Bearer {second_user_with_profile['token']}"}
		client.post(
			"/projects",
			json={"title": "User2", "category": "frontend"},
			headers=headers_user2
		)

		get_response = client.get(f"/projects/{project_id_user1}", headers=headers_user2)
		assert get_response.status_code == status.HTTP_403_FORBIDDEN

		update_response = client.put(
			f"/projects/{project_id_user1}",
			json={"title": "Hacked"},
			headers=headers_user2
		)
		assert update_response.status_code == status.HTTP_403_FORBIDDEN

		delete_response = client.delete(f"/projects/{project_id_user1}", headers=headers_user2)
		assert delete_response.status_code == status.HTTP_403_FORBIDDEN

		list_response = client.get("/projects/me", headers=headers_user2)
		data = list_response.json()
		assert len(data) == 1
		assert data[0]["title"] == "User2"

	# --- TEST DE FLUJO COMPLETO ---

	def test_complete_project_flow(self, client: TestClient):
		"""Test: Flujo completo - Registro, Login, Crear Perfil, CRUD Proyectos"""
		register_data = {
			"username": "flowproject",
			"email": "flowproject@example.com",
			"password": "password123"
		}
		register_response = client.post("/auth/register", json=register_data)
		assert register_response.status_code == status.HTTP_201_CREATED

		login_data = {
			"username": "flowproject@example.com",
			"password": "password123"
		}
		login_response = client.post("/auth/login", data=login_data)
		assert login_response.status_code == status.HTTP_200_OK
		token = login_response.json()["access_token"]
		headers = {"Authorization": f"Bearer {token}"}

		profile_data = {
			"name": "Flow",
			"last_name": "Project",
			"current_title": "DevOps Engineer"
		}
		profile_response = client.post("/profile", json=profile_data, headers=headers)
		assert profile_response.status_code == status.HTTP_201_CREATED

		tech_id = client.post(
			"/technologies",
			json={"name": "Docker", "category": "dev_tools"},
			headers=headers
		).json()["id"]

		project_data = {
			"title": "Pipeline",
			"category": "backend",
			"technology_ids": [tech_id],
			"previews": [
				{"image_url": "https://img.com/pipe.png", "caption": "CI", "order": 1}
			]
		}
		create_response = client.post("/projects", json=project_data, headers=headers)
		assert create_response.status_code == status.HTTP_201_CREATED
		project_id = create_response.json()["id"]

		get_response = client.get(f"/projects/{project_id}", headers=headers)
		assert get_response.status_code == status.HTTP_200_OK

		list_response = client.get("/projects/me", headers=headers)
		assert list_response.status_code == status.HTTP_200_OK
		assert len(list_response.json()) == 1

		update_response = client.put(
			f"/projects/{project_id}",
			json={"title": "Pipeline CI/CD"},
			headers=headers
		)
		assert update_response.status_code == status.HTTP_200_OK
		assert update_response.json()["title"] == "Pipeline CI/CD"

		delete_response = client.delete(f"/projects/{project_id}", headers=headers)
		assert delete_response.status_code == status.HTTP_204_NO_CONTENT

		list_after = client.get("/projects/me", headers=headers)
		assert list_after.status_code == status.HTTP_200_OK
		assert list_after.json() == []
