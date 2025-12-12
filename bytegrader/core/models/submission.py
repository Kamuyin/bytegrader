from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, UniqueConstraint, func, \
    CheckConstraint, case, and_, Enum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from . import Grade
from .base import Base, new_uuid
from .enum import SubmissionStatus
from ..utils import utc_now


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(32), primary_key=True, default=new_uuid)
    assignment_id = Column(String(32), ForeignKey('assignments.id'), nullable=False)
    user_id = Column(String(128), ForeignKey('users.id'), nullable=False)

    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.SUBMITTED, nullable=False)
    submitted_at = Column(DateTime)
    extension_days = Column(Integer, default=0, nullable=False)

    graded_at = Column(DateTime)
    graded_by = Column(String(128))

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    assignment = relationship("Assignment", back_populates="submissions")
    user = relationship("User", back_populates="submissions")
    notebook_submissions = relationship("NotebookSubmission", back_populates="submission",
                                        cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('extension_days >= 0', name='positive_extension'),
    )

    @hybrid_property
    def effective_due_date(self):
        if self.assignment.due_date and self.extension_days > 0:
            return self.assignment.due_date + timedelta(days=self.extension_days)
        return self.assignment.due_date

    @hybrid_property
    def is_late(self):
        if not self.submitted_at or not self.effective_due_date:
            return False

        due = self.effective_due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)

        submitted = self.submitted_at
        if submitted.tzinfo is None:
            submitted = submitted.replace(tzinfo=timezone.utc)

        return submitted > due

    @hybrid_property
    def days_late(self):
        if not self.is_late:
            return 0

        due = self.effective_due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)

        submitted = self.submitted_at
        if submitted.tzinfo is None:
            submitted = submitted.replace(tzinfo=timezone.utc)

        delta = submitted - due
        return max(0, delta.days)

    @hybrid_property
    def total_score(self):
        if not self.notebook_submissions:
            return 0.0
        total = 0.0
        for nb_sub in self.notebook_submissions:
            for grade in nb_sub.grades:
                total += grade.final_score
        return total

    @total_score.expression
    def total_score(cls):
        from sqlalchemy import select
        return select(func.coalesce(func.sum(
            case(
                (Grade.manual_score.isnot(None), Grade.manual_score),
                else_=func.coalesce(Grade.auto_score, 0.0)
            ) + func.coalesce(Grade.extra_credit, 0.0)
        ), 0.0)) \
            .select_from(
            NotebookSubmission.__table__.join(Grade.__table__)
        ) \
            .where(NotebookSubmission.submission_id == cls.id) \
            .scalar_subquery()

    @hybrid_property
    def auto_score(self):
        if not self.notebook_submissions:
            return 0.0
        total = 0.0
        for nb_sub in self.notebook_submissions:
            for grade in nb_sub.grades:
                if grade.auto_score is not None:
                    total += grade.auto_score + (grade.extra_credit or 0.0)
        return total

    @auto_score.expression
    def auto_score(cls):
        from sqlalchemy import select
        return select(func.coalesce(func.sum(
            func.coalesce(Grade.auto_score, 0.0) + func.coalesce(Grade.extra_credit, 0.0)
        ), 0.0)) \
            .select_from(
            NotebookSubmission.__table__.join(Grade.__table__)
        ) \
            .where(
            and_(
                NotebookSubmission.submission_id == cls.id,
                Grade.auto_score.isnot(None)
            )
        ) \
            .scalar_subquery()

    @hybrid_property
    def manual_score(self):
        if not self.notebook_submissions:
            return 0.0
        total = 0.0
        for nb_sub in self.notebook_submissions:
            for grade in nb_sub.grades:
                if grade.manual_score is not None:
                    total += grade.manual_score + (grade.extra_credit or 0.0)
        return total

    @manual_score.expression
    def manual_score(cls):
        from sqlalchemy import select
        return select(func.coalesce(func.sum(
            func.coalesce(Grade.manual_score, 0.0) + func.coalesce(Grade.extra_credit, 0.0)
        ), 0.0)) \
            .select_from(
            NotebookSubmission.__table__.join(Grade.__table__)
        ) \
            .where(
            and_(
                NotebookSubmission.submission_id == cls.id,
                Grade.manual_score.isnot(None)
            )
        ) \
            .scalar_subquery()

    @hybrid_property
    def needs_manual_grading(self):
        if not self.notebook_submissions:
            return True
        for nb_sub in self.notebook_submissions:
            for grade in nb_sub.grades:
                if grade.needs_manual_grading:
                    return True
        return False

    @needs_manual_grading.expression
    def needs_manual_grading(cls):
        from sqlalchemy import select, exists
        return select(
            exists().where(
                and_(
                    NotebookSubmission.submission_id == cls.id,
                    Grade.notebook_submission_id == NotebookSubmission.id,
                    Grade.needs_manual_grading == True
                )
            )
        ).scalar_subquery()

    def __repr__(self):
        return f"Submission(id='{self.id}', user='{self.user_id}', assignment='{self.assignment.name}')"


class NotebookSubmission(Base):
    __tablename__ = "notebook_submissions"

    id = Column(String(32), primary_key=True, default=new_uuid)
    submission_id = Column(String(32), ForeignKey('submissions.id'), nullable=False)
    notebook_id = Column(String(32), ForeignKey('notebooks.id'), nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    submission = relationship("Submission", back_populates="notebook_submissions")
    notebook = relationship("Notebook", back_populates="notebook_submissions")
    cell_submissions = relationship("CellSubmission", back_populates="notebook_submission",
                                    cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="notebook_submission", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="notebook_submission", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('submission_id', 'notebook_id'),
    )

    @hybrid_property
    def total_score(self):
        if not self.grades:
            return 0.0
        return sum(grade.final_score for grade in self.grades)

    @total_score.expression
    def total_score(cls):
        from sqlalchemy import select
        return select(func.coalesce(func.sum(
            case(
                (Grade.manual_score.isnot(None), Grade.manual_score),
                else_=func.coalesce(Grade.auto_score, 0.0)
            ) + func.coalesce(Grade.extra_credit, 0.0)
        ), 0.0)) \
            .where(Grade.notebook_submission_id == cls.id) \
            .scalar_subquery()

    @hybrid_property
    def auto_score(self):
        if not self.grades:
            return 0.0
        return sum(
            (grade.auto_score or 0.0) + (grade.extra_credit or 0.0)
            for grade in self.grades
            if grade.auto_score is not None
        )

    @auto_score.expression
    def auto_score(cls):
        from sqlalchemy import select
        return select(func.coalesce(func.sum(
            func.coalesce(Grade.auto_score, 0.0) + func.coalesce(Grade.extra_credit, 0.0)
        ), 0.0)) \
            .where(
            and_(
                Grade.notebook_submission_id == cls.id,
                Grade.auto_score.isnot(None)
            )
        ) \
            .scalar_subquery()

    @hybrid_property
    def manual_score(self):
        if not self.grades:
            return 0.0
        return sum(
            (grade.manual_score or 0.0) + (grade.extra_credit or 0.0)
            for grade in self.grades
            if grade.manual_score is not None
        )

    @manual_score.expression
    def manual_score(cls):
        from sqlalchemy import select
        return select(func.coalesce(func.sum(
            func.coalesce(Grade.manual_score, 0.0) + func.coalesce(Grade.extra_credit, 0.0)
        ), 0.0)) \
            .where(
            and_(
                Grade.notebook_submission_id == cls.id,
                Grade.manual_score.isnot(None)
            )
        ) \
            .scalar_subquery()

    @hybrid_property
    def needs_manual_grading(self):
        if not self.grades:
            return True
        return any(grade.needs_manual_grading for grade in self.grades)

    @needs_manual_grading.expression
    def needs_manual_grading(cls):
        from sqlalchemy import select, exists
        return select(
            exists().where(
                and_(
                    Grade.notebook_submission_id == cls.id,
                    Grade.needs_manual_grading == True
                )
            )
        ).scalar_subquery()

    def __repr__(self):
        return f"NotebookSubmission(id='{self.id}', notebook='{self.notebook.name}')"


class CellSubmission(Base):
    __tablename__ = "cell_submissions"

    id = Column(String(32), primary_key=True, default=new_uuid)
    notebook_submission_id = Column(String(32), ForeignKey('notebook_submissions.id'), nullable=False)
    cell_id = Column(String(128), ForeignKey('cells.id'), nullable=False)

    submitted_source = Column(Text)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    notebook_submission = relationship("NotebookSubmission", back_populates="cell_submissions")
    cell = relationship("Cell")

    __table_args__ = (
        UniqueConstraint('notebook_submission_id', 'cell_id'),
    )