from typing import Optional

import cloudinary
import cloudinary.uploader

from src.infrastructure.config import settings


class CloudinaryService:
	def __init__(self):
		cloudinary.config(
			cloud_name=settings.cloudinary_cloud_name,
			api_key=settings.cloudinary_api_key,
			api_secret=settings.cloudinary_api_secret,
			secure=True
		)

	def upload_image(self, file, folder: Optional[str] = None, public_id: Optional[str] = None) -> str:
		"""
		Sube una imagen a Cloudinary y retorna la URL segura.
		Aplica optimizaciones automáticas para reducir tiempo de subida.
		"""
		result = cloudinary.uploader.upload(
			file,
			folder=folder,
			public_id=public_id,
			resource_type="image",
			# Optimizaciones para acelerar la subida
			quality="auto:good",  # Calidad automática optimizada
			fetch_format="auto",  # Formato óptimo automático
			timeout=60  # Timeout de 60 segundos para Cloudinary
		)
		return result["secure_url"]
