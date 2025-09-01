from typing import List

from ..core.models import AssignmentAsset as AssignmentAssetModel
from .base import BaseRepository


class AssignmentAssetRepository(BaseRepository[AssignmentAssetModel]):
    def __init__(self, db_manager):
        super().__init__(AssignmentAssetModel, db_manager)

    def list_by_assignment(self, assignment_id: str) -> List[AssignmentAssetModel]:
        with self.db_manager.get_session() as session:
            return session.query(self.model).filter_by(assignment_id=assignment_id).all()