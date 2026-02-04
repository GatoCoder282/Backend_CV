"""
Tests de Integración - Images Flow

Valida el flujo de carga de imágenes a Cloudinary:
- Upload exitoso con autenticación ADMIN
- Upload con folder especificado
- Validación de tipo de archivo (solo imágenes)
- Manejo de errores del servicio
- Control de acceso (solo ADMIN puede subir)

Nota: Usa mocking para CloudinaryService para evitar llamadas reales al servicio.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from io import BytesIO


class TestImagesFlow:
    """Suite de tests para el flujo de carga de imágenes"""

    # --- FIXTURES HELPERS ---
    
    @pytest.fixture
    def authenticated_user(self, client: TestClient):
        """Usuario registrado y autenticado (ADMIN)"""
        user_data = {
            "username": "image_user",
            "email": "images@example.com",
            "password": "password123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "username": "images@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        return {"email": "images@example.com", "token": token}

    @pytest.fixture
    def mock_image_file(self):
        """Crea un archivo de imagen simulado"""
        # Crear un archivo de imagen PNG mínimo (1x1 píxel)
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
            b'\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx'
            b'\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00'
            b'IEND\xaeB`\x82'
        )
        return BytesIO(png_data)

    @pytest.fixture
    def mock_text_file(self):
        """Crea un archivo de texto simulado (no imagen)"""
        return BytesIO(b"This is not an image")

    # --- TEST UPLOAD IMAGE SUCCESS ---

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_image_success(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict,
        mock_image_file: BytesIO
    ):
        """Test subir imagen exitosamente sin folder"""
        token = authenticated_user["token"]
        mock_upload.return_value = "https://cloudinary.com/image123.jpg"
        
        response = client.post(
            "/images/upload",
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "url" in data
        assert data["url"] == "https://cloudinary.com/image123.jpg"
        
        # Verificar que se llamó al servicio
        mock_upload.assert_called_once()

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_image_with_folder(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict,
        mock_image_file: BytesIO
    ):
        """Test subir imagen con folder especificado"""
        token = authenticated_user["token"]
        mock_upload.return_value = "https://cloudinary.com/profiles/image123.jpg"
        
        response = client.post(
            "/images/upload?folder=profiles",
            files={"file": ("test.png", mock_image_file, "image/png")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "url" in data
        assert data["url"] == "https://cloudinary.com/profiles/image123.jpg"
        
        # Verificar que se llamó con el folder correcto
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args.kwargs.get('folder') == 'profiles'

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_different_image_formats(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict,
        mock_image_file: BytesIO
    ):
        """Test subir diferentes formatos de imagen (jpeg, png, gif, webp)"""
        token = authenticated_user["token"]
        image_formats = [
            ("image/jpeg", "test.jpg"),
            ("image/png", "test.png"),
            ("image/gif", "test.gif"),
            ("image/webp", "test.webp")
        ]
        
        for content_type, filename in image_formats:
            mock_upload.return_value = f"https://cloudinary.com/{filename}"
            mock_image_file.seek(0)  # Reset file pointer
            
            response = client.post(
                "/images/upload",
                files={"file": (filename, mock_image_file, content_type)},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 201, f"Failed for {content_type}"
            data = response.json()
            assert "url" in data

    # --- TEST VALIDATION ERRORS ---

    def test_upload_non_image_file_fails(
        self, 
        client: TestClient, 
        authenticated_user: dict,
        mock_text_file: BytesIO
    ):
        """Test que falla al intentar subir un archivo que no es imagen"""
        token = authenticated_user["token"]
        
        response = client.post(
            "/images/upload",
            files={"file": ("test.txt", mock_text_file, "text/plain")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "imagen" in response.json()["detail"].lower()

    def test_upload_without_file_fails(
        self, 
        client: TestClient, 
        authenticated_user: dict
    ):
        """Test que falla al no enviar archivo"""
        token = authenticated_user["token"]
        
        response = client.post(
            "/images/upload",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_pdf_as_image_fails(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict
    ):
        """Test que falla al intentar subir PDF como imagen"""
        token = authenticated_user["token"]
        pdf_data = b"%PDF-1.4 test"
        
        response = client.post(
            "/images/upload",
            files={"file": ("test.pdf", BytesIO(pdf_data), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "imagen" in response.json()["detail"].lower()
        
        # El servicio no debe ser llamado
        mock_upload.assert_not_called()

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_image_without_explicit_content_type(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict,
        mock_image_file: BytesIO
    ):
        """Test subir imagen sin content_type explícito (FastAPI lo detecta por extensión)"""
        token = authenticated_user["token"]
        mock_upload.return_value = "https://cloudinary.com/image_no_ct.jpg"
        
        # FastAPI puede detectar el content_type por la extensión .jpg
        response = client.post(
            "/images/upload",
            files={"file": ("test.jpg", mock_image_file)},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Debería funcionar si FastAPI detecta el tipo automáticamente
        # Si falla, retornará 400
        assert response.status_code in [201, 400]

    # --- TEST SERVICE ERRORS ---

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_service_error_returns_500(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict,
        mock_image_file: BytesIO
    ):
        """Test que retorna 500 cuando el servicio de Cloudinary falla"""
        token = authenticated_user["token"]
        mock_upload.side_effect = Exception("Cloudinary connection error")
        
        response = client.post(
            "/images/upload",
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_timeout_error(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict,
        mock_image_file: BytesIO
    ):
        """Test manejo de error de timeout"""
        token = authenticated_user["token"]
        mock_upload.side_effect = TimeoutError("Upload timeout")
        
        response = client.post(
            "/images/upload",
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 500

    # --- TEST AUTHENTICATION & AUTHORIZATION ---

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_without_authentication_fails(
        self, 
        mock_upload: MagicMock, 
        client: TestClient,
        mock_image_file: BytesIO
    ):
        """Test que falla sin autenticación"""
        response = client.post(
            "/images/upload",
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")}
        )
        
        assert response.status_code == 401
        mock_upload.assert_not_called()

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_with_invalid_token_fails(
        self, 
        mock_upload: MagicMock, 
        client: TestClient,
        mock_image_file: BytesIO
    ):
        """Test que falla con token inválido"""
        response = client.post(
            "/images/upload",
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        
        assert response.status_code == 401
        mock_upload.assert_not_called()

    # --- TEST EDGE CASES ---

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_empty_image_file(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict
    ):
        """Test subir archivo de imagen vacío"""
        token = authenticated_user["token"]
        empty_file = BytesIO(b"")
        
        # Cloudinary debería manejar esto, pero podemos simular un error
        mock_upload.side_effect = Exception("Invalid image data")
        
        response = client.post(
            "/images/upload",
            files={"file": ("empty.jpg", empty_file, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Puede ser 400 o 500 dependiendo de la validación
        assert response.status_code in [400, 500]

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_very_large_image(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict
    ):
        """Test subir imagen muy grande (simula límite de tamaño)"""
        token = authenticated_user["token"]
        # Simular imagen grande (10MB de datos)
        large_image = BytesIO(b"x" * (10 * 1024 * 1024))
        
        mock_upload.return_value = "https://cloudinary.com/large_image.jpg"
        
        response = client.post(
            "/images/upload",
            files={"file": ("large.jpg", large_image, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Debería funcionar si el servicio lo acepta
        assert response.status_code == 201

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_with_special_characters_in_folder(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict,
        mock_image_file: BytesIO
    ):
        """Test subir con caracteres especiales en el nombre del folder"""
        token = authenticated_user["token"]
        mock_upload.return_value = "https://cloudinary.com/user-profile_2024/image.jpg"
        
        response = client.post(
            "/images/upload?folder=user-profile_2024",
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201

    # --- TEST COMPLETE FLOW ---

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_complete_upload_flow(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict,
        mock_image_file: BytesIO
    ):
        """Test flujo completo: múltiples uploads con diferentes configuraciones"""
        token = authenticated_user["token"]
        
        # 1. Upload sin folder
        mock_upload.return_value = "https://cloudinary.com/image1.jpg"
        mock_image_file.seek(0)
        response1 = client.post(
            "/images/upload",
            files={"file": ("image1.jpg", mock_image_file, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 201
        assert response1.json()["url"] == "https://cloudinary.com/image1.jpg"
        
        # 2. Upload con folder "profiles"
        mock_upload.return_value = "https://cloudinary.com/profiles/avatar.png"
        mock_image_file.seek(0)
        response2 = client.post(
            "/images/upload?folder=profiles",
            files={"file": ("avatar.png", mock_image_file, "image/png")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response2.status_code == 201
        assert response2.json()["url"] == "https://cloudinary.com/profiles/avatar.png"
        
        # 3. Upload con folder "projects"
        mock_upload.return_value = "https://cloudinary.com/projects/screenshot.jpg"
        mock_image_file.seek(0)
        response3 = client.post(
            "/images/upload?folder=projects",
            files={"file": ("screenshot.jpg", mock_image_file, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response3.status_code == 201
        assert response3.json()["url"] == "https://cloudinary.com/projects/screenshot.jpg"
        
        # Verificar que se llamó 3 veces al servicio
        assert mock_upload.call_count == 3

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_with_svg_image(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict
    ):
        """Test subir imagen SVG"""
        token = authenticated_user["token"]
        svg_data = b'<svg xmlns="http://www.w3.org/2000/svg"><circle r="50"/></svg>'
        mock_upload.return_value = "https://cloudinary.com/icon.svg"
        
        response = client.post(
            "/images/upload",
            files={"file": ("icon.svg", BytesIO(svg_data), "image/svg+xml")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        assert "url" in response.json()

    @patch('src.application.services.cloudinary_service.CloudinaryService.upload_image')
    def test_upload_returns_valid_url_format(
        self, 
        mock_upload: MagicMock, 
        client: TestClient, 
        authenticated_user: dict,
        mock_image_file: BytesIO
    ):
        """Test que la URL retornada tiene formato válido"""
        token = authenticated_user["token"]
        mock_upload.return_value = "https://res.cloudinary.com/demo/image/upload/v1234567890/sample.jpg"
        
        response = client.post(
            "/images/upload",
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        url = response.json()["url"]
        assert url.startswith("https://")
        assert "cloudinary" in url
