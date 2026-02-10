from typing import Optional
import os
import re
import unicodedata
from datetime import datetime

from supabase import create_client, Client

from src.infrastructure.config import settings


class SupabaseService:
	def __init__(self):
		self.client: Client = create_client(
			settings.supabase_url,
			settings.supabase_service_key  # Usa service_key para operaciones de backend
		)
		self.bucket_name = settings.supabase_bucket_name

	def _sanitize_filename(self, filename: str) -> str:
		"""
		Limpia el nombre del archivo para Supabase Storage:
		- Elimina acentos y caracteres especiales
		- Reemplaza espacios por guiones bajos
		- Convierte a lowercase
		"""
		# Normalizar caracteres unicode (eliminar acentos)
		filename = unicodedata.normalize('NFKD', filename)
		filename = filename.encode('ASCII', 'ignore').decode('ASCII')
		
		# Reemplazar espacios y caracteres especiales por guiones bajos
		filename = re.sub(r'[^\w\.-]', '_', filename)
		
		# Eliminar múltiples guiones bajos consecutivos
		filename = re.sub(r'_+', '_', filename)
		
		# Convertir a lowercase para consistencia
		filename = filename.lower()
		
		return filename

	def upload_pdf(
		self,
		file_bytes: bytes,
		filename: str,
		folder: Optional[str] = None
	) -> str:
		"""
		Sube un PDF a Supabase Storage y retorna la URL pública.
		
		Args:
			file_bytes: Contenido del archivo en bytes
			filename: Nombre del archivo (debe incluir .pdf)
			folder: Carpeta opcional dentro del bucket
		
		Returns:
			URL pública del archivo subido
		"""
		try:
			# Sanitizar el nombre del archivo
			clean_filename = self._sanitize_filename(filename)
			
			# Generar nombre único con timestamp
			timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
			unique_filename = f"{timestamp}_{clean_filename}"
			
			# Construir path completo
			if folder:
				file_path = f"{folder}/{unique_filename}"
			else:
				file_path = unique_filename
			
			# Subir archivo a Supabase Storage
			response = self.client.storage.from_(self.bucket_name).upload(
				path=file_path,
				file=file_bytes,
				file_options={
					"content-type": "application/pdf",
					"cache-control": "3600",
					"upsert": "false"  # No sobrescribir si existe
				}
			)
			
			# Obtener URL pública
			public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
			
			return public_url
			
		except Exception as e:
			raise Exception(f"Error al subir PDF a Supabase: {str(e)}")

	def delete_pdf(self, file_path: str) -> bool:
		"""
		Elimina un PDF de Supabase Storage.
		
		Args:
			file_path: Ruta del archivo dentro del bucket (sin el nombre del bucket)
		
		Returns:
			True si se eliminó correctamente
		"""
		try:
			self.client.storage.from_(self.bucket_name).remove([file_path])
			return True
		except Exception as e:
			raise Exception(f"Error al eliminar PDF de Supabase: {str(e)}")

	def get_pdf_url(self, file_path: str) -> str:
		"""
		Obtiene la URL pública de un PDF existente.
		
		Args:
			file_path: Ruta del archivo dentro del bucket
		
		Returns:
			URL pública del archivo
		"""
		return self.client.storage.from_(self.bucket_name).get_public_url(file_path)
