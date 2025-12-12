from datetime import datetime, timedelta

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func, \
    CheckConstraint, Float, Enum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, validates

from .base import Base, new_uuid
from .enum import CellType
from ..utils import utc_now


class Notebook(Base):
    __tablename__ = "notebooks"

    id = Column(String(32), primary_key=True, default=new_uuid)
    assignment_id = Column(String(32), ForeignKey('assignments.id'), nullable=False)
    name = Column(String(256), nullable=False)
    idx = Column(Integer, nullable=False)  # Order within assignment
    kernelspec = Column(Text)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    assignment = relationship("Assignment", back_populates="notebooks")
    cells = relationship("Cell", back_populates="notebook",
                         cascade="all, delete-orphan", order_by="Cell.idx")
    notebook_submissions = relationship(
        "NotebookSubmission",
        back_populates="notebook",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint('assignment_id', 'name'),
        UniqueConstraint('assignment_id', 'idx'),
        CheckConstraint('idx >= 0', name='positive_idx'),
    )

    @hybrid_property
    def max_score(self):
        if not self.cells:
            return 0.0
        return sum(cell.max_score for cell in self.cells)

    @max_score.expression
    def max_score(cls):
        from sqlalchemy import select
        return select(func.coalesce(func.sum(Cell.max_score), 0.0)) \
            .where(Cell.notebook_id == cls.id) \
            .scalar_subquery()

    def __repr__(self):
        return f"Notebook(id='{self.id}', name='{self.name}')"


class Cell(Base):
    __tablename__ = "cells"

    id = Column(String(128), primary_key=True)  # Jupyter's native cell ID
    notebook_id = Column(String(32), ForeignKey('notebooks.id'), nullable=False)
    name = Column(String(256), nullable=True)  # Optional display name, fallback to cell_id
    idx = Column(Integer, nullable=False)  # Order within notebook
    cell_type = Column(Enum(CellType), nullable=False)

    source = Column(Text)
    source_student = Column(Text)
    meta = Column(Text)

    max_score = Column(Float, default=0.0, nullable=False)

    is_grade = Column(Boolean, default=False, nullable=False)
    is_solution = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    is_task = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    notebook = relationship("Notebook", back_populates="cells")
    grades = relationship("Grade", back_populates="cell")
    comments = relationship("Comment", back_populates="cell")

    __table_args__ = (
        UniqueConstraint('notebook_id', 'id'),
        UniqueConstraint('notebook_id', 'idx'),
        CheckConstraint('max_score >= 0', name='positive_max_score'),
        CheckConstraint('idx >= 0', name='positive_idx'),

        CheckConstraint('(is_grade = true) OR (max_score = 0)', name='gradable_score_consistency'),
    )

    @validates('max_score')
    def validate_max_score(self, key, value):
        if value < 0:
            raise ValueError("max_score must be non-negative")
        return value

    def __repr__(self):
        return f"Cell(cell_id='{self.cell_id}', type='{self.cell_type.value}')"
