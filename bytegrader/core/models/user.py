from datetime import datetime, timedelta

from sqlalchemy import Column, String, Integer, Enum, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from .base import Base, new_uuid
from .enum import UserRole
from ..utils import utc_now


class User(Base):
    __tablename__ = "users"

    id = Column(String(128), primary_key=True)
    first_name = Column(String(128))
    last_name = Column(String(128))
    email = Column(String(256)) # * Won't be passed via LTI since the LTI-Authenticator for JupyterHub wants to use the email as the username for some reason which won't work with systemd.
    lms_user_id = Column(String(128))
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="user")

    @hybrid_property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.id

    def __repr__(self):
        return f"User(id='{self.id}', name='{self.full_name}')"


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint('user_id', 'course_id'),)

    id = Column(String(32), primary_key=True, default=new_uuid)
    user_id = Column(String(128), ForeignKey('users.id'), nullable=False)
    course_id = Column(String(128), ForeignKey('courses.label'),
                       nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    enrolled_at = Column(DateTime, default=utc_now, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
