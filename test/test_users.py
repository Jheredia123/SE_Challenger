import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.main import app
from app.database import Base, get_db

# --- CONFIGURACIÓN DE LA BASE DE DATOS DE PRUEBAS ---
# Usamos una base de datos SQLite independiente para no ensuciar la de desarrollo
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Sobrescribe la dependencia de la BD para usar la de pruebas."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Inyectamos la base de datos de pruebas en la aplicación
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """
    Fixture que se ejecuta antes y después de cada test.
    Garantiza que cada prueba inicie con una base de datos limpia.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# --- SUITE DE PRUEBAS ---

def test_create_user():
    """Prueba la creación exitosa de un usuario."""
    payload = {
        "username": "Jordan Heredia",
        "email": "jordan.heredia@example.com",
        "first_name": "Software",
        "last_name": "Engineer",
        "role": "admin",
        "active": True
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == payload["username"]
    assert "id" in data


def test_read_users():
    """Prueba la obtención de la lista de usuarios (paginación)."""
    # Creamos un usuario previo
    client.post("/users/", json={
        "username": "user1", "email": "u1@ex.com",
        "first_name": "N", "last_name": "L", "role": "user"
    })

    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_read_user_by_id():
    """Prueba obtener un usuario específico por su ID."""
    create_res = client.post("/users/", json={
        "username": "find_me", "email": "find@ex.com",
        "first_name": "F", "last_name": "M", "role": "user"
    })
    user_id = create_res.json()["id"]

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["username"] == "find_me"


def test_read_user_not_found():
    """Prueba el caso de error 404 para un usuario inexistente."""
    response = client.get("/users/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuario no encontrado"


def test_update_user():
    """Prueba la actualización parcial (PATCH/PUT) de un usuario."""
    create_res = client.post("/users/", json={
        "username": "old_username", "email": "old@ex.com",
        "first_name": "Old", "last_name": "Name", "role": "guest"
    })
    user_id = create_res.json()["id"]

    # Actualizamos solo el primer nombre y el rol
    update_payload = {"first_name": "New", "role": "admin"}
    response = client.put(f"/users/{user_id}", json=update_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "New"
    assert data["role"] == "admin"
    assert data["username"] == "old_username"  # Se mantiene intacto


def test_delete_user():
    """Prueba el ciclo de eliminación de un usuario."""
    # Crear
    create_res = client.post("/users/", json={
        "username": "delete_me", "email": "del@ex.com",
        "first_name": "D", "last_name": "U", "role": "user"
    })
    user_id = create_res.json()["id"]

    # Eliminar
    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 204

    # Verificar inexistencia
    verify_response = client.get(f"/users/{user_id}")
    assert verify_response.status_code == 404