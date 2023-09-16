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

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(Integer, primary_key=True, index=True)
    detection_enabled = Column(Boolean, default=True)

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, index=True)
    time = Column(DateTime)
    video = Column(String)
    preview = Column(String)
    notification_sent = Column(Boolean, default=False)
    viewed = Column(Boolean, default=False)
    description = Column(String)