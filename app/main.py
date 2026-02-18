import logging
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import engine, get_db

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- INICIALIZACIÓN DE BASE DE DATOS ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User Management API",
    description="API robusta para la gestión de usuarios - Challenge Software Engineer",
    version="1.0.0"
)


# --- ENDPOINTS ---

@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario validando que no existan duplicados.

    Args:
        user (schemas.UserCreate): Datos del nuevo usuario.
        db (Session): Sesión de base de datos inyectada.

    Returns:
        schemas.User: El usuario creado exitosamente.

    Raises:
        HTTPException: Si el username o email ya están registrados (400).
    """
    logger.info(f"Intentando crear usuario: {user.username}")

    # Validar existencia previa por username
    if crud.get_user_by_username(db, username=user.username):
        logger.warning(f"Conflicto: El username '{user.username}' ya existe.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado."
        )

    # Validar existencia previa por email
    if crud.get_user_by_email(db, email=user.email):
        logger.warning(f"Conflicto: El email '{user.email}' ya existe.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado."
        )

    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtiene la lista de usuarios con soporte para paginación."""
    return crud.get_users(db, skip=skip, limit=limit)


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Obtiene un usuario específico por su ID único."""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"Usuario con ID {user_id} no encontrado")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    """Actualiza parcialmente los datos de un usuario existente."""
    logger.info(f"Actualizando usuario ID: {user_id}")
    db_user = crud.update_user(db, user_id=user_id, user_update=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Elimina permanentemente un usuario del sistema."""
    logger.info(f"Eliminando usuario ID: {user_id}")
    success = crud.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return None