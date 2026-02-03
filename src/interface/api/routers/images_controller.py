from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from typing import Optional

from src.application.services.cloudinary_service import CloudinaryService
from src.interface.api.authorization import get_current_admin
from src.domain.entities import User

router = APIRouter(prefix="/images", tags=["Images"])


def get_cloudinary_service() -> CloudinaryService:
	return CloudinaryService()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
	file: UploadFile = File(...),
	folder: Optional[str] = None,
	current_user: User = Depends(get_current_admin),
	service: CloudinaryService = Depends(get_cloudinary_service)
):
	"""
	Sube una imagen a Cloudinary y devuelve la URL.
	Solo ADMIN puede subir.
	"""
	if not file.content_type or not file.content_type.startswith("image/"):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="El archivo debe ser una imagen."
		)

	try:
		file_bytes = await file.read()
		url = service.upload_image(file_bytes, folder=folder)
		return {"url": url}
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Error al subir imagen: {str(e)}"
		)
