from typing import List
from sqlalchemy.orm import selectinload

from ..core.exceptions import DatabaseError
from ..core.models.course import Assignment as AssignmentModel
from ..core.models.notebook import Notebook
from .base import BaseRepository


class AssignmentRepository(BaseRepository[AssignmentModel]):
    def __init__(self, db_manager):
        super().__init__(AssignmentModel, db_manager)

    def get_by_course_and_name(self, course_id: str, name: str) -> AssignmentModel:
        with self.db_manager.get_session() as session:
            try:
                return session.query(self.model) \
                    .filter_by(course_id=course_id, name=name) \
                    .first()
            except Exception as e:
                raise DatabaseError(f"Failed to retrieve assignment '{name}' for course '{course_id}': {e}") from e

    def get_by_course(self, course_id: str) -> List[AssignmentModel]:
        with self.db_manager.get_session() as session:
            try:
                return (
                    session.query(self.model)
                    .options(
                        selectinload(AssignmentModel.course),
                        selectinload(AssignmentModel.notebooks)
                        .selectinload(Notebook.cells)
                    )
                    .filter_by(course_id=course_id)
                    .all()
                )
            except Exception as e:
                raise DatabaseError(f"Failed to retrieve assignments for course '{course_id}': {e}") from e
