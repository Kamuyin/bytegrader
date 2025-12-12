import re
from typing import Any, Dict, Tuple
import nbformat
from ..base import BaseProcessor
from ...core.utils import notebook as utils


class ClearHiddenTestsProcessor(BaseProcessor):
    def __init__(self, config: Dict[str, Any] = None, **kw):
        super().__init__(config, **kw)

        self.begin_delimiter = self.params.get('begin_delimiter', 'BEGIN HIDDEN TESTS')
        self.end_delimiter = self.params.get('end_delimiter', 'END HIDDEN TESTS')
        self.enforce_metadata = self.params.get('enforce_metadata', True)

    def preprocess(self, nb: nbformat.NotebookNode, resources: Dict[str, Any]) -> Tuple[
        nbformat.NotebookNode, Dict[str, Any]]:

        for i, cell in enumerate(nb.cells):
            self._process_cell(cell, i)

        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']

        return nb, resources

    def _process_cell(self, cell: nbformat.NotebookNode, cell_index: int):
        if isinstance(cell.source, list):
            cell.source = ''.join(cell.source)
        elif not isinstance(cell.source, str):
            cell.source = str(cell.source)

        is_grade_cell = utils.is_grade(cell)
        has_hidden_test_region = self._remove_hidden_test_region(cell)

        if has_hidden_test_region and not is_grade_cell and self.enforce_metadata:
            self.log.error(f"Cell {cell_index} has hidden test region but is not marked as a grade cell")
            raise ValueError(f"Hidden test region found in non-grade cell at index {cell_index}")

    def _remove_hidden_test_region(self, cell: nbformat.NotebookNode) -> bool:
        lines = cell.source.split('\n')
        new_lines = []
        in_test = False
        found_test = False

        for line in lines:
            if self.begin_delimiter in line:
                if in_test:
                    raise ValueError("Nested BEGIN HIDDEN TESTS found")

                in_test = True
                found_test = True
            elif self.end_delimiter in line:
                if not in_test:
                    raise ValueError("END HIDDEN TESTS without BEGIN HIDDEN TESTS")
                in_test = False
            elif not in_test:
                new_lines.append(line)

        if in_test:
            raise ValueError("BEGIN HIDDEN TESTS without END HIDDEN TESTS")

        if found_test:
            cell.source = '\n'.join(new_lines)

        return found_test