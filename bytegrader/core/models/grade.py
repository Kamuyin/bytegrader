from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, \
    CheckConstraint, Float
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from .base import Base, new_uuid
from ..utils import utc_now


class Grade(Base):
    __tablename__ = "grades"

    id = Column(String(32), primary_key=True, default=new_uuid)
    notebook_submission_id = Column(String(32), ForeignKey('notebook_submissions.id'), nullable=False)
    cell_id = Column(String(128), ForeignKey('cells.id'), nullable=False)

    auto_score = Column(Float)
    manual_score = Column(Float)
    extra_credit = Column(Float, default=0.0, nullable=False)

    needs_manual_grading = Column(Boolean, default=True, nullable=False)
    execution_error = Column(Text, nullable=True)
    graded_at = Column(DateTime)
    graded_by = Column(String(128))

    notebook_submission = relationship("NotebookSubmission", back_populates="grades")
    cell = relationship("Cell", back_populates="grades")

    __table_args__ = (
        UniqueConstraint('notebook_submission_id', 'id'),
        UniqueConstraint('notebook_submission_id', 'cell_id', name='uq_grade_cell_submission'),
        CheckConstraint('auto_score IS NULL OR auto_score >= 0', name='positive_auto_score'),
        CheckConstraint('manual_score IS NULL OR manual_score >= 0', name='positive_manual_score'),
    )

    @hybrid_property
    def final_score(self):
        base_score = self.manual_score if self.manual_score is not None else (self.auto_score or 0.0)
        return base_score + (self.extra_credit or 0.0)

    def __repr__(self):
        return f"Grade(id='{self.id}', cell='{self.cell.display_name}', score={self.final_score})"


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String(32), primary_key=True, default=new_uuid)
    notebook_submission_id = Column(String(32), ForeignKey('notebook_submissions.id'), nullable=False)
    cell_id = Column(String(128), ForeignKey('cells.id'), nullable=False)

    auto_comment = Column(Text)
    manual_comment = Column(Text)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    commented_by = Column(String(128))  # Who made the manual comment

    notebook_submission = relationship("NotebookSubmission", back_populates="comments")
    cell = relationship("Cell", back_populates="comments")

    __table_args__ = (
        UniqueConstraint('notebook_submission_id', 'cell_id'),
    )

    @hybrid_property
    def final_comment(self):
        return self.manual_comment or self.auto_comment

    def __repr__(self):
        return f"Comment(id='{self.id}', cell='{self.cell.display_name}')"