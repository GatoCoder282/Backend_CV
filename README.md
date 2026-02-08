# Backend CV - Portfolio API

**Versión:** 1.0.0 | **Estado:** Producción Ready ✅

API Backend para el portfolio de Diego Valdez, desarrollada con **FastAPI** siguiendo **Clean Architecture (Arquitectura Hexagonal)**.

## 🏗️ Arquitectura

```
Hexagonal Architecture
├── Domain Layer          # Lógica pura de negocio (entities, exceptions)
├── Application Layer     # Casos de uso (services, DTOs)
├── Infrastructure Layer  # Implementaciones técnicas (repos, BD, config)
└── Interface Layer       # Adaptadores (API controllers, security)
```

## 🚀 Tecnologías

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Framework | FastAPI | 0.128.0 |
| ORM | SQLModel + SQLAlchemy | 2.0.43 |
| Autenticación | JWT + Argon2 | python-jose 3.5.0 |
| Validación | Pydantic | 2.12.5 |
| Migraciones | Alembic | 1.14.0 |
| BD (Prod) | PostgreSQL | 13+ |
| Almacenamiento | Cloudinary | 1.44.1 |
| Tests | Pytest | 8.3.5 |
| Python | 3.12+ | - |

## 📋 Estructura del Proyecto

```
Backend_CV/
├── src/
│   ├── domain/               # Entidades y lógica pura
│   │   ├── entities.py       # Dataclasses con validaciones
│   │   ├── exceptions.py     # Excepciones de negocio
│   │   └── ports.py          # Interfaces/Puertos (ABC)
│   ├── application/          # Casos de uso
│   │   ├── services/         # Lógica de negocio orquestada
│   │   └── dtos/            # Schemas Pydantic (Input/Output)
│   ├── infrastructure/       # Implementaciones técnicas
│   │   ├── config.py         # Settings y variables de entorno
│   │   ├── security.py       # JWT + Argon2 (Adaptadores)
│   │   ├── data_base/        # Motor, modelos, conexión
│   │   └── repositories/     # Implementación de puertos
│   ├── interface/
│   │   ├── api/
│   │   │   ├── routers/      # Endpoints (controladores)
│   │   │   └── authorization.py # Dependencias JWT
│   │   └── main.py           # App FastAPI
├── test/                     # Tests de integración
├── alembic/                  # Migraciones de BD
├── .env.example              # Variables de entorno (PLANTILLA)
├── requirements.txt          # Dependencias
└── README.md                 # Este archivo
```

## 🔐 Seguridad (IMPORTANTE)

### Variables de Entorno
1. **Copiar** `.env.example` → `.env`
2. **Generar** `SECRET_KEY` seguro:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
3. **NUNCA** commitear `.env` (ya está en `.gitignore`)

### Headers de Seguridad
✅ X-Content-Type-Options: nosniff  
✅ X-Frame-Options: DENY  
✅ X-XSS-Protection: 1; mode=block  
✅ Strict-Transport-Security (HTTPS en prod)

### CORS
- ✅ Desarrollo: localhost:3000, localhost:5173
- ✅ Producción: Solo dominios específicos (actualizar en `main.py`)

### Autenticación
- ✅ JWT con Argon2 para hashing
- ✅ Roles: ADMIN, SUPERADMIN
- ✅ Token expiry: 30 minutos (configurable)

## ⚙️ Instalación (Desarrollo Local)

### Paso 1: Clonar y preparar entorno
```bash
git clone <URL_REPOSITORIO>
cd Backend_CV
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### Paso 2: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Configurar variables
```bash
cp .env.example .env
# Editar .env con tus valores (DATABASE_URL, SECRET_KEY, etc.)
```

### Paso 4: Preparar base de datos
```bash
# Primera vez: crear esquema
alembic upgrade head

# O resetear (desarrollo):
rm portfolio.db 2>/dev/null || true
python -c "from src.infrastructure.data_base.main import create_db_and_tables; create_db_and_tables()"
```

## 🏃 Ejecución

### Desarrollo (con hot-reload)
```bash
fastapi dev src/main.py
```

### Producción (sin reload)
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Acceso
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Tests

```bash
# Ejecutar todos
pytest

# Con cobertura
pytest --cov=src --cov-report=html

# Tests específicos
pytest test/integration_test/test_authentication_flow.py -v
```

## 📦 Dependencias Principales

Ver [requirements.txt](requirements.txt) para versiones exactas.

**Core:**
- fastapi >= 0.128.0
- uvicorn[standard]
- sqlmodel
- sqlalchemy >= 2.0

**Autenticación:**
- python-jose[cryptography]
- passlib[argon2]
- email-validator

**Infraestructura:**
- pydantic-settings
- python-dotenv
- cloudinary
- alembic
- psycopg[binary] (PostgreSQL)

## 📚 Endpoints Principales

### Auth
```
POST   /auth/register     → Crear usuario
POST   /auth/login        → Obtener JWT token
GET    /auth/me           → Datos del usuario (requiere JWT)
GET    /auth/public/{username} → Info pública del usuario
```

### Perfil
```
GET    /profiles/{user_id}   → Obtener perfil
POST   /profiles             → Crear perfil (ADMIN)
PUT    /profiles/{id}        → Actualizar (ADMIN + propietario)
DELETE /profiles/{id}        → Eliminar (ADMIN + propietario)
```

### Proyectos, Tecnologías, Experiencia
- **GET** (público): Consultar datos
- **POST/PUT/DELETE** (ADMIN): Crear/editar/eliminar

### Imágenes
```
POST /images/upload        → Subir imagen a Cloudinary
POST /images/upload-pdf    → Subir PDF
```

**Documentación completa:** http://localhost:8000/docs

## ✅ Checklist Producción

Se debe completar ANTES de hacer deploy:

- [ ] SECRET_KEY generado con `secrets.token_hex(32)`
- [ ] DATABASE_URL apunta a PostgreSQL en producción
- [ ] CORS configurado para dominio exacto
- [ ] Credenciales Cloudinary en variables no hardcodeadas
- [ ] HTTPS habilitado (Nginx / Gunicorn)
- [ ] Health check `/` respondiendo
- [ ] Tests pasar 100% (`pytest --cov`)
- [ ] Logs configurados y rotando
- [ ] Backups BD automáticos
- [ ] Monitoreo de errores (Sentry, etc.)

## 👨‍💻 Autor

**Diego Valdez**  
Portfolio API Backend - Clean Architecture  
Contacto: diegomvaldez19@gmail.com

## 📝 Licencia

Privado - Personal Use Only
