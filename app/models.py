from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from .database import Base
from datetime import datetime, timezone
import enum


class UserRole(enum.Enum):
    """Enumeración de roles de usuario según los requisitos del desafío."""
    admin = "admin"
    user = "user"
    guest = "guest"


class User(Base):
    """Modelo de base de datos para la entidad Usuario."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.user)

    # Marcadores de tiempo (Timestamps) corregidos para Python 3.12+
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    active = Column(Boolean, default=True)