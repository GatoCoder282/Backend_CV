from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from src.interface.api.routers import auth_controller, profile_controller, project_controller, technology_controller, work_experience_controller, client_controller, social_controller, images_controller

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portfolio_api")

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando Portfolio API...")
    # Las tablas se crean via Alembic, no aquí
    yield
    logger.info("🛑 Apagando servicios...")

# --- APP ---
app = FastAPI(
    title="Diego Valdez Portfolio API",
    description="Clean Architecture Backend",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url="/openapi.json",  # Documentación en /docs
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS ---
from src.infrastructure.config import settings

# En producción, especificar origins exactos
if settings.environment == "prod":
    origins = [
        "https://frontend-cv-ten.vercel.app",
    ]
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,  # Cache preflight por 10 min
)

# --- SECURITY HEADERS ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    return response

# --- EXCEPTION HANDLING ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para excepciones no manejadas.
    En desarrollo: devuelve el error completo.
    En producción: devuelve error genérico por seguridad.
    """
    logger.error(f"Excepción no manejada: {exc}", exc_info=True)
    
    if settings.environment == "prod":
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor. Por favor intenta más tarde."}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )

# --- ROUTERS ---
app.include_router(auth_controller.router)
app.include_router(profile_controller.router)
app.include_router(project_controller.router)
app.include_router(technology_controller.router)
app.include_router(work_experience_controller.router)
app.include_router(client_controller.router)
app.include_router(social_controller.router)
app.include_router(images_controller.router)

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Bienvenido a la API del Portafolio de Diego Valdez", 
        "mode": "Dev",
        "docs_url": "/docs"
    }

# YA NO NECESITAS EL BLOQUE "if __name__ == '__main__': uvicorn.run..."