# Backend CV - Portfolio API

API Backend para el portfolio de Diego Valdez, desarrollada con FastAPI siguiendo principios de Clean Architecture.

## 🚀 Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **SQLModel** - ORM para SQL databases con Pydantic
- **Pydantic** - Validación de datos
- **SQLAlchemy** - Motor y utilidades de base de datos
- **JWT (python-jose)** - Autenticación y autorización
- **Passlib (Argon2)** - Hashing de contraseñas
- **Cloudinary** - Almacenamiento de imágenes
- **Python 3.12+**

## 📋 Estructura del Proyecto

```
Backend_CV/
├── src/
│   ├── domain/          # Entidades y lógica de negocio
│   ├── application/     # Casos de uso
│   └── infrastructure/  # Implementaciones técnicas
│       ├── config.py
│       ├── data_base/
│       └── repositories/
├── src/main.py         # Punto de entrada de la aplicación
└── requirements.txt    # Dependencias del proyecto
```

## ⚙️ Instalación

1. Clonar el repositorio:
```bash
git clone <URL_REPOSITORIO>
cd Backend_CV
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
Crear archivo `.env` en la raíz del proyecto (puedes partir de `.env.example`) con:
```env
DATABASE_URL=sqlite:///./portfolio.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SUPERADMIN_EMAIL=your-email@example.com
ENVIRONMENT=dev
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## 🏃 Ejecución

```bash
uvicorn src.main:app --reload
```

También puedes usar FastAPI CLI:

```bash
fastapi dev src/main.py
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

## ✅ Tests

```bash
pytest
```

## 👨‍💻 Autor

**Diego Valdez**
- Portfolio API Backend

## 📝 Licencia

Este proyecto es privado.
