from datetime import datetime, timedelta

from sqlalchemy import Column, String, Integer, Enum, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from .base import Base, new_uuid
from .enum import ShowSolutionsOption
from .notebook import Notebook
from ..utils import utc_now


class AssignmentAsset(Base):
    __tablename__ = "assignment_assets"

    id = Column(String(32), primary_key=True, default=new_uuid)
    assignment_id = Column(String(32), ForeignKey('assignments.id'), nullable=False)
    path = Column(Text, nullable=False)  # Relative path
    size = Column(Integer)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    assignment = relationship("Assignment", back_populates="assets")

    __table_args__ = (
        UniqueConstraint('assignment_id', 'path'),
    )

    def __repr__(self):
        return f"AssignmentAsset(id='{self.id}', assignment_id='{self.assignment_id}', path='{self.path}')"
