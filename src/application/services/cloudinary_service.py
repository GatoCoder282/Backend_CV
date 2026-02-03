import os
from typing import Optional

import cloudinary
import cloudinary.uploader


class CloudinaryService:
	def __init__(self):
		cloudinary.config(
			cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
			api_key=os.getenv("CLOUDINARY_API_KEY"),
			api_secret=os.getenv("CLOUDINARY_API_SECRET"),
			secure=True
		)

	def upload_image(self, file, folder: Optional[str] = None, public_id: Optional[str] = None) -> str:
		"""
		Sube una imagen a Cloudinary y retorna la URL segura.
		"""
		result = cloudinary.uploader.upload(
			file,
			folder=folder,
			public_id=public_id,
			resource_type="image"
		)
		return result["secure_url"]
