import nbformat
from typing import Any, Dict, Tuple
from ..base import BaseProcessor
from ...core.utils import notebook as utils


class LockCellsProcessor(BaseProcessor):

    def __init__(self, config: Dict[str, Any] = None, **kw):
        super().__init__(config, **kw)

        self.lock_solution_cells = self.params.get('lock_solution_cells', True)
        self.lock_grade_cells = self.params.get('lock_grade_cells', True)
        self.lock_locked_cells = self.params.get('lock_locked_cells', True)
        self.lock_all_cells = self.params.get('lock_all_cells', False)

    def preprocess(self, nb: nbformat.NotebookNode, resources: Dict[str, Any]) -> Tuple[
        nbformat.NotebookNode, Dict[str, Any]]:
        for i, cell in enumerate(nb.cells):
            self._process_cell(cell, i)

        return nb, resources

    def _process_cell(self, cell: nbformat.NotebookNode, cell_index: int):
        is_solution = utils.is_solution(cell)
        is_grade = utils.is_grade(cell)
        is_locked = utils.is_locked(cell)

        if self.lock_all_cells:
            cell.metadata['deletable'] = False
            cell.metadata['editable'] = False

        elif (self.lock_solution_cells or self.lock_grade_cells) and is_solution and is_grade:
            cell.metadata['deletable'] = False

        elif self.lock_solution_cells and is_solution:
            cell.metadata['deletable'] = False

        elif self.lock_grade_cells and is_grade:
            cell.metadata['deletable'] = False
            cell.metadata['editable'] = False

        elif self.lock_locked_cells and is_locked:
            cell.metadata['deletable'] = False
            cell.metadata['editable'] = False
