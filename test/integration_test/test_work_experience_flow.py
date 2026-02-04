"""
Tests de Integración - Work Experience Flow

Cobertura:
- Creación con/sin perfil, con/sin auth, validación de fechas
- Listado de experiencias propias (orden por start_date desc)
- Obtención por ID con ownership
- Actualización parcial y validación de fechas
- Eliminación (soft delete)
- Aislamiento multi-tenant
- Flujo completo
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestWorkExperienceFlow:
	"""Suite de tests para el flujo completo de Work Experience"""

	@pytest.fixture
	def authenticated_user(self, client: TestClient):
		"""Usuario registrado y autenticado"""
		user_data = {
			"username": "work_user",
			"email": "work@example.com",
			"password": "password123"
		}
		client.post("/auth/register", json=user_data)

		login_data = {
			"username": "work@example.com",
			"password": "password123"
		}
		response = client.post("/auth/login", data=login_data)
		token = response.json()["access_token"]
		return {"email": "work@example.com", "token": token}

	@pytest.fixture
	def user_with_profile(self, client: TestClient, authenticated_user):
		"""Usuario con perfil creado (requerido para work experience)"""
		profile_data = {
			"name": "Work",
			"last_name": "Owner",
			"current_title": "Backend Developer"
		}
		headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
		client.post("/profile", json=profile_data, headers=headers)
		return authenticated_user

	@pytest.fixture
	def second_user_with_profile(self, client: TestClient):
		"""Segundo usuario para pruebas multi-tenant"""
		user_data = {
			"username": "work_user2",
			"email": "work2@example.com",
			"password": "password123"
		}
		client.post("/auth/register", json=user_data)

		login_data = {
			"username": "work2@example.com",
			"password": "password123"
		}
		response = client.post("/auth/login", data=login_data)
		token = response.json()["access_token"]

		profile_data = {
			"name": "Work2",
			"last_name": "Owner2",
			"current_title": "Frontend Developer"
		}
		headers = {"Authorization": f"Bearer {token}"}
		client.post("/profile", json=profile_data, headers=headers)

		return {"email": "work2@example.com", "token": token}

	# --- TESTS DE CREACIÓN ---

	def test_create_work_experience_success(self, client: TestClient, user_with_profile):
		"""Test: Crear experiencia laboral exitosamente"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		work_data = {
			"job_title": "Software Engineer",
			"company": "Tech Corp",
			"location": "Remote",
			"start_date": "2022-01-01",
			"end_date": "2023-01-01",
			"description": "Backend development"
		}

		response = client.post("/work-experience", json=work_data, headers=headers)

		assert response.status_code == status.HTTP_201_CREATED
		data = response.json()
		assert data["job_title"] == "Software Engineer"
		assert data["company"] == "Tech Corp"
		assert data["location"] == "Remote"
		assert data["start_date"] == "2022-01-01"
		assert data["end_date"] == "2023-01-01"
		assert data["description"] == "Backend development"
		assert "id" in data
		assert "profile_id" in data

	def test_create_work_experience_without_profile_fails(self, client: TestClient, authenticated_user):
		"""Test: Crear experiencia sin perfil falla"""
		headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
		work_data = {
			"job_title": "Engineer",
			"company": "NoProfile Inc",
			"start_date": "2021-01-01"
		}

		response = client.post("/work-experience", json=work_data, headers=headers)

		assert response.status_code == status.HTTP_400_BAD_REQUEST
		assert "perfil" in response.json()["detail"].lower()

	def test_create_work_experience_without_auth_fails(self, client: TestClient):
		"""Test: Crear experiencia sin autenticación falla"""
		work_data = {
			"job_title": "Engineer",
			"company": "NoAuth Inc",
			"start_date": "2021-01-01"
		}

		response = client.post("/work-experience", json=work_data)

		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	def test_create_work_experience_missing_required_fields_fails(self, client: TestClient, user_with_profile):
		"""Test: Crear experiencia sin campos requeridos falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		work_data = {
			"job_title": "Engineer"
			# Falta company y start_date
		}

		response = client.post("/work-experience", json=work_data, headers=headers)

		assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

	def test_create_work_experience_invalid_dates_fails(self, client: TestClient, user_with_profile):
		"""Test: Crear experiencia con end_date anterior falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		work_data = {
			"job_title": "Engineer",
			"company": "Tech",
			"start_date": "2023-01-01",
			"end_date": "2022-01-01"
		}

		response = client.post("/work-experience", json=work_data, headers=headers)

		assert response.status_code == status.HTTP_400_BAD_REQUEST
		assert "fecha" in response.json()["detail"].lower()

	# --- TESTS DE LISTADO ---

	def test_get_my_work_experiences_success(self, client: TestClient, user_with_profile):
		"""Test: Obtener lista de mis experiencias (orden start_date desc)"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

		create_1 = client.post(
			"/work-experience",
			json={
				"job_title": "Junior",
				"company": "Acme",
				"start_date": "2020-01-01"
			},
			headers=headers
		)
		assert create_1.status_code == status.HTTP_201_CREATED, create_1.json()

		create_2 = client.post(
			"/work-experience",
			json={
				"job_title": "Senior",
				"company": "Beta",
				"start_date": "2022-01-01"
			},
			headers=headers
		)
		assert create_2.status_code == status.HTTP_201_CREATED, create_2.json()

		response = client.get("/work-experience/me", headers=headers)

		assert response.status_code == status.HTTP_200_OK
		data = response.json()
		assert len(data) == 2
		assert data[0]["job_title"] == "Senior"
		assert data[1]["job_title"] == "Junior"

	def test_get_my_work_experiences_empty_list(self, client: TestClient, user_with_profile):
		"""Test: Obtener lista vacía cuando no hay experiencias"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}

		response = client.get("/work-experience/me", headers=headers)

		assert response.status_code == status.HTTP_200_OK
		assert response.json() == []

	def test_get_my_work_experiences_without_auth_fails(self, client: TestClient):
		"""Test: Obtener experiencias sin autenticación falla"""
		response = client.get("/work-experience/me")
		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	# --- TESTS DE OBTENCIÓN POR ID ---

	def test_get_work_experience_by_id_success(self, client: TestClient, user_with_profile):
		"""Test: Obtener experiencia por ID exitosamente"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/work-experience",
			json={
				"job_title": "Engineer",
				"company": "Tech",
				"start_date": "2021-01-01"
			},
			headers=headers
		)
		work_id = create_response.json()["id"]

		response = client.get(f"/work-experience/{work_id}", headers=headers)

		assert response.status_code == status.HTTP_200_OK
		data = response.json()
		assert data["id"] == work_id
		assert data["job_title"] == "Engineer"

	def test_get_work_experience_nonexistent_id_fails(self, client: TestClient, user_with_profile):
		"""Test: Obtener experiencia inexistente falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		response = client.get("/work-experience/99999", headers=headers)

		assert response.status_code == status.HTTP_404_NOT_FOUND

	def test_get_work_experience_without_auth_fails(self, client: TestClient, user_with_profile):
		"""Test: Obtener experiencia sin autenticación falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/work-experience",
			json={
				"job_title": "Engineer",
				"company": "Tech",
				"start_date": "2021-01-01"
			},
			headers=headers
		)
		work_id = create_response.json()["id"]

		response = client.get(f"/work-experience/{work_id}")

		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	# --- TESTS DE ACTUALIZACIÓN ---

	def test_update_work_experience_success(self, client: TestClient, user_with_profile):
		"""Test: Actualizar experiencia exitosamente"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/work-experience",
			json={
				"job_title": "Developer",
				"company": "Tech",
				"start_date": "2020-01-01"
			},
			headers=headers
		)
		work_id = create_response.json()["id"]

		update_data = {
			"job_title": "Senior Developer",
			"company": "Tech Corp",
			"end_date": "2022-12-31",
			"description": "Liderando proyectos"
		}

		response = client.put(f"/work-experience/{work_id}", json=update_data, headers=headers)

		assert response.status_code == status.HTTP_200_OK
		data = response.json()
		assert data["job_title"] == "Senior Developer"
		assert data["company"] == "Tech Corp"
		assert data["end_date"] == "2022-12-31"
		assert data["description"] == "Liderando proyectos"

	def test_update_work_experience_partial_update(self, client: TestClient, user_with_profile):
		"""Test: Actualización parcial mantiene campos no enviados"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/work-experience",
			json={
				"job_title": "Developer",
				"company": "Tech",
				"location": "Remote",
				"start_date": "2020-01-01"
			},
			headers=headers
		)
		work_id = create_response.json()["id"]

		response = client.put(
			f"/work-experience/{work_id}",
			json={"location": "Hybrid"},
			headers=headers
		)

		assert response.status_code == status.HTTP_200_OK
		data = response.json()
		assert data["job_title"] == "Developer"
		assert data["company"] == "Tech"
		assert data["location"] == "Hybrid"

	def test_update_work_experience_invalid_dates_fails(self, client: TestClient, user_with_profile):
		"""Test: Actualizar experiencia con fechas inválidas falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/work-experience",
			json={
				"job_title": "Developer",
				"company": "Tech",
				"start_date": "2020-01-01"
			},
			headers=headers
		)
		work_id = create_response.json()["id"]

		response = client.put(
			f"/work-experience/{work_id}",
			json={"start_date": "2022-01-01", "end_date": "2021-01-01"},
			headers=headers
		)

		assert response.status_code == status.HTTP_400_BAD_REQUEST
		assert "fecha" in response.json()["detail"].lower()

	def test_update_work_experience_nonexistent_id_fails(self, client: TestClient, user_with_profile):
		"""Test: Actualizar experiencia inexistente falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		response = client.put(
			"/work-experience/99999",
			json={"job_title": "Valid"},
			headers=headers
		)

		assert response.status_code == status.HTTP_404_NOT_FOUND

	def test_update_work_experience_without_auth_fails(self, client: TestClient, user_with_profile):
		"""Test: Actualizar experiencia sin autenticación falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/work-experience",
			json={
				"job_title": "Developer",
				"company": "Tech",
				"start_date": "2020-01-01"
			},
			headers=headers
		)
		work_id = create_response.json()["id"]

		response = client.put(f"/work-experience/{work_id}", json={"job_title": "No"})

		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	# --- TESTS DE ELIMINACIÓN ---

	def test_delete_work_experience_success(self, client: TestClient, user_with_profile):
		"""Test: Eliminar experiencia exitosamente"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/work-experience",
			json={
				"job_title": "Developer",
				"company": "Tech",
				"start_date": "2020-01-01"
			},
			headers=headers
		)
		work_id = create_response.json()["id"]

		response = client.delete(f"/work-experience/{work_id}", headers=headers)

		assert response.status_code == status.HTTP_204_NO_CONTENT

		list_response = client.get("/work-experience/me", headers=headers)
		assert list_response.status_code == status.HTTP_200_OK
		assert list_response.json() == []

	def test_delete_work_experience_nonexistent_id_fails(self, client: TestClient, user_with_profile):
		"""Test: Eliminar experiencia inexistente falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		response = client.delete("/work-experience/99999", headers=headers)

		assert response.status_code == status.HTTP_404_NOT_FOUND

	def test_delete_work_experience_without_auth_fails(self, client: TestClient, user_with_profile):
		"""Test: Eliminar experiencia sin autenticación falla"""
		headers = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/work-experience",
			json={
				"job_title": "Developer",
				"company": "Tech",
				"start_date": "2020-01-01"
			},
			headers=headers
		)
		work_id = create_response.json()["id"]

		response = client.delete(f"/work-experience/{work_id}")

		assert response.status_code == status.HTTP_401_UNAUTHORIZED

	# --- TESTS MULTI-TENANT ---

	def test_work_experience_multi_tenant_isolation(
		self,
		client: TestClient,
		user_with_profile,
		second_user_with_profile
	):
		"""Test: Usuarios solo pueden ver/modificar sus propias experiencias"""
		headers_user1 = {"Authorization": f"Bearer {user_with_profile['token']}"}
		create_response = client.post(
			"/work-experience",
			json={
				"job_title": "User1",
				"company": "Acme",
				"start_date": "2020-01-01"
			},
			headers=headers_user1
		)
		assert create_response.status_code == status.HTTP_201_CREATED, create_response.json()
		work_id_user1 = create_response.json()["id"]

		headers_user2 = {"Authorization": f"Bearer {second_user_with_profile['token']}"}
		create_user2 = client.post(
			"/work-experience",
			json={
				"job_title": "User2",
				"company": "Beta",
				"start_date": "2021-01-01"
			},
			headers=headers_user2
		)
		assert create_user2.status_code == status.HTTP_201_CREATED, create_user2.json()

		get_response = client.get(f"/work-experience/{work_id_user1}", headers=headers_user2)
		assert get_response.status_code == status.HTTP_403_FORBIDDEN

		update_response = client.put(
			f"/work-experience/{work_id_user1}",
			json={"job_title": "Hacked"},
			headers=headers_user2
		)
		assert update_response.status_code == status.HTTP_403_FORBIDDEN

		delete_response = client.delete(f"/work-experience/{work_id_user1}", headers=headers_user2)
		assert delete_response.status_code == status.HTTP_403_FORBIDDEN

		list_response = client.get("/work-experience/me", headers=headers_user2)
		data = list_response.json()
		assert len(data) == 1
		assert data[0]["job_title"] == "User2"

	# --- TEST DE FLUJO COMPLETO ---

	def test_complete_work_experience_flow(self, client: TestClient):
		"""Test: Flujo completo - Registro, Login, Crear Perfil, CRUD Work Experience"""
		register_data = {
			"username": "flowwork",
			"email": "flowwork@example.com",
			"password": "password123"
		}
		register_response = client.post("/auth/register", json=register_data)
		assert register_response.status_code == status.HTTP_201_CREATED

		login_data = {
			"username": "flowwork@example.com",
			"password": "password123"
		}
		login_response = client.post("/auth/login", data=login_data)
		assert login_response.status_code == status.HTTP_200_OK
		token = login_response.json()["access_token"]
		headers = {"Authorization": f"Bearer {token}"}

		profile_data = {
			"name": "Flow",
			"last_name": "Work",
			"current_title": "QA Engineer"
		}
		profile_response = client.post("/profile", json=profile_data, headers=headers)
		assert profile_response.status_code == status.HTTP_201_CREATED

		work_data = {
			"job_title": "QA",
			"company": "Test Inc",
			"start_date": "2021-01-01",
			"description": "Automation"
		}
		create_response = client.post("/work-experience", json=work_data, headers=headers)
		assert create_response.status_code == status.HTTP_201_CREATED
		work_id = create_response.json()["id"]

		get_response = client.get(f"/work-experience/{work_id}", headers=headers)
		assert get_response.status_code == status.HTTP_200_OK

		list_response = client.get("/work-experience/me", headers=headers)
		assert list_response.status_code == status.HTTP_200_OK
		assert len(list_response.json()) == 1

		update_response = client.put(
			f"/work-experience/{work_id}",
			json={"job_title": "Senior QA"},
			headers=headers
		)
		assert update_response.status_code == status.HTTP_200_OK
		assert update_response.json()["job_title"] == "Senior QA"

		delete_response = client.delete(f"/work-experience/{work_id}", headers=headers)
		assert delete_response.status_code == status.HTTP_204_NO_CONTENT

		list_after = client.get("/work-experience/me", headers=headers)
		assert list_after.status_code == status.HTTP_200_OK
		assert list_after.json() == []
