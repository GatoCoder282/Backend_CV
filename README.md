# Backend CV - Portfolio API

API Backend para el portfolio de Diego Valdez, desarrollada con FastAPI siguiendo principios de Clean Architecture.

## 🚀 Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **SQLModel** - ORM para SQL databases con Pydantic
- **Pydantic** - Validación de datos
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
├── main.py             # Punto de entrada de la aplicación
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
Crear archivo `.env` en la raíz del proyecto con:
```env
DATABASE_URL=sqlite:///./portfolio.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=dev
```

## 🏃 Ejecución

```bash
uvicorn main:app --reload
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

## 👨‍💻 Autor

**Diego Valdez**
- Portfolio API Backend

## 📝 Licencia

Este proyecto es privado.
