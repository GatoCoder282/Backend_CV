from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.infrastructure.data_base.main import create_db_and_tables
from src.interface.api.routers import auth_controller as auth

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Iniciando Portfolio API con FastAPI CLI...")
    create_db_and_tables()
    yield
    print("🛑 Apagando servicios...")

# --- APP ---
app = FastAPI(
    title="Diego Valdez Portfolio API",
    description="Backend Hexagonal corriendo con 'fastapi dev'",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS ---
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
app.include_router(auth.router)

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Bienvenido a la API del Portafolio de Diego Valdez", 
        "mode": "Dev",
        "docs_url": "/docs"
    }

# YA NO NECESITAS EL BLOQUE "if __name__ == '__main__': uvicorn.run..."