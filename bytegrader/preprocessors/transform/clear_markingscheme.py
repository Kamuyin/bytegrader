import re
from typing import Any, Dict, Tuple
import nbformat
from ..base import BaseProcessor
from ...core.utils import notebook as utils


class ClearMarkSchemeProcessor(BaseProcessor):
    def __init__(self, config: Dict[str, Any] = None, **kw):
        super().__init__(config, **kw)

        self.begin_delimiter = self.params.get('begin_delimiter', 'BEGIN MARK SCHEME')
        self.end_delimiter = self.params.get('end_delimiter', 'END MARK SCHEME')
        self.enforce_metadata = self.params.get('enforce_metadata', True)
        self.check_attachment_leakage = self.params.get('check_attachment_leakage', True)

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

        is_task_cell = utils.is_task(cell)
        has_mark_scheme_region = self._remove_mark_scheme_region(cell)

        if has_mark_scheme_region and not is_task_cell and self.enforce_metadata:
            self.log.error(f"Cell {cell_index} has mark scheme region but is not marked as a task cell")
            raise ValueError(f"Mark scheme region found in non-task cell at index {cell_index}")

    def _remove_mark_scheme_region(self, cell: nbformat.NotebookNode) -> bool:
        lines = cell.source.split('\n')
        new_lines = []
        in_mark_scheme = False
        found_mark_scheme = False
        attachment_regex = r"!\[.*\]\(attachment:.+?\)"

        for line in lines:
            if self.begin_delimiter in line:
                if in_mark_scheme:
                    raise ValueError("Nested BEGIN MARK SCHEME found")

                in_mark_scheme = True
                found_mark_scheme = True
            elif self.end_delimiter in line:
                if not in_mark_scheme:
                    raise ValueError("END MARK SCHEME without BEGIN MARK SCHEME")
                in_mark_scheme = False
            elif in_mark_scheme and self.check_attachment_leakage and re.search(attachment_regex, line):
                raise ValueError(
                    "Attachment found in mark scheme region. This can leak to student notebooks. "
                    "Consider embedding your image or disable this check with check_attachment_leakage=False."
                )
            elif not in_mark_scheme:
                new_lines.append(line)

        if in_mark_scheme:
            raise ValueError("BEGIN MARK SCHEME without END MARK SCHEME")

        if found_mark_scheme:
            cell.source = '\n'.join(new_lines)

        return found_mark_scheme
