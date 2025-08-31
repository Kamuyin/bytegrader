from typing import List

from sqlalchemy.orm import joinedload

from ..core.models import Submission as SubmissionModel, NotebookSubmission
from ..core.models.enum import SubmissionStatus
from .base import BaseRepository


class SubmissionRepository(BaseRepository[SubmissionModel]):
    def __init__(self, db_manager):
        super().__init__(SubmissionModel, db_manager)

    def list_for_user_and_assignments(self, user_id: str, assignment_ids: list[str], include_archived: bool = False):
        with self.db_manager.get_session() as session:
            query = (
                session.query(SubmissionModel)
                .options(
                    joinedload(SubmissionModel.assignment),
                    joinedload(SubmissionModel.notebook_submissions).joinedload(
                        NotebookSubmission.grades
                    ),
                )
                .filter(
                    SubmissionModel.user_id == user_id,
                    SubmissionModel.assignment_id.in_(assignment_ids)
                )
            )
            
            if not include_archived:
                query = query.filter(SubmissionModel.status != SubmissionStatus.ARCHIVED)
            
            return query.all()
