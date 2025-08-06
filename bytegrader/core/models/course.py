from datetime import datetime, timedelta

from sqlalchemy import Column, String, Integer, Enum, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from .base import Base, new_uuid
from .enum import ShowSolutionsOption
from .notebook import Notebook
from ..utils import utc_now


class Course(Base):
    __tablename__ = "courses"

    label = Column(String(128), primary_key=True)
    title = Column(String(256), nullable=False)
    lti_id = Column(String(64), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Course(label='{self.label}', title='{self.title}')"


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(32), primary_key=True, default=new_uuid)
    course_id = Column(String(128), ForeignKey('courses.label'),
                       nullable=False)
    name = Column(String(256), nullable=False)
    description = Column(Text)
    lti_id = Column(String(32), nullable=True)
    due_date = Column(DateTime)
    allow_resubmission = Column(Boolean, default=False, nullable=False)
    allow_late_submission = Column(Boolean, default=False, nullable=False)
    show_solutions = Column(
        Enum(ShowSolutionsOption, name="show_solutions_option"),
        default=ShowSolutionsOption.NEVER,
        nullable=False
    )
    visible = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    course = relationship("Course", back_populates="assignments")
    notebooks = relationship("Notebook", back_populates="assignment",
                             cascade="all, delete-orphan", order_by="Notebook.idx")
    submissions = relationship(
        "Submission",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )
    assets = relationship(
        'AssignmentAsset',
        back_populates='assignment',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        UniqueConstraint('course_id', 'name'),
    )

    @hybrid_property
    def max_score(self):
        if not self.notebooks:
            return 0.0
        return sum(notebook.max_score for notebook in self.notebooks)

    @max_score.expression
    def max_score(cls):
        from sqlalchemy import select
        return select(func.coalesce(func.sum(Notebook.max_score), 0.0)) \
            .where(Notebook.assignment_id == cls.id) \
            .scalar_subquery()

    def __repr__(self):
        return f"Assignment(id='{self.id}', name='{self.name}')"

