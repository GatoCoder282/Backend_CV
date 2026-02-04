# test/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from src.main import app
from src.infrastructure.data_base.main import get_session
from src.infrastructure.data_base.models import (
    UserModel,
    ProfileModel,
    WorkExperienceModel,
    ProjectModel,
    TechnologyModel,
    ClientModel,
    SocialModel
)
# O simplemente:
# import src.infrastructure.data_base.models

# Usamos SQLite en memoria para que sea rápido y aislado
sqlite_file_name = "sqlite:///:memory:"
engine = create_engine(
    sqlite_file_name,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(name="session")
def session_fixture():
    # Ahora sí, SQLModel sabe qué tablas existen y las creará correctamente
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # Borrar todo al terminar
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()