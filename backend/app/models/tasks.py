from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, relationship, DeclarativeBase
from app.database import Base
import enum


class Priority(str, enum.Enum):
    """Only allow these values for priority."""
    low = "low"
    medium = "medium"
    high = "high"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


     # relationships
    tasks: Mapped[list["Task"]] = relationship(back_populates="user")



class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description =Column(String(2000), nullable=True)
    priority = Column(Enum(Priority), nullable=True)
    completed = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # relationships
    user: Mapped["User"]= relationship(back_populates="tasks")

   

