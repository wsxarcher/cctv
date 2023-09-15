from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
import secrets
import enum

from .database import Base, SessionLocal, engine
from sqlalchemy_utils import PasswordType, force_auto_coercion

force_auto_coercion()

class StreamingMethod(enum.Enum):
    hls = 1
    mjpeg = 2

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(PasswordType(
        schemes=[
            'pbkdf2_sha512',
        ],
    ))
    streaming_method = Column(Enum(StreamingMethod), default=StreamingMethod.hls)

    sessions = relationship("Session", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"
    token = Column(String, index=True, unique=True, primary_key=True)
    user_agent = Column(String)
    ip = Column(String)
    login_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="sessions")
