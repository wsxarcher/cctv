from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
import secrets

from .database import Base, SessionLocal, engine
from sqlalchemy_utils import PasswordType, force_auto_coercion

force_auto_coercion()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(PasswordType(
        schemes=[
            'pbkdf2_sha512',
        ],
    ))

    sessions = relationship("Session", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"
    token = Column(String, index=True, unique=True, primary_key=True)
    user_agent = Column(String)
    ip = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="sessions")
