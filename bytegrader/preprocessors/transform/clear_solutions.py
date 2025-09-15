import re
import nbformat
from typing import Any, Dict, Tuple
from ..base import BaseProcessor
from ...core.utils import notebook as utils


class ClearSolutionsProcessor(BaseProcessor):
    def __init__(self, config: Dict[str, Any] = None, **kw):
        super().__init__(config, **kw)

        self.code_stubs = self.params.get('code_stubs', {
            'python': '# YOUR CODE HERE\nraise NotImplementedError()',
            'r': '# YOUR CODE HERE\nfail()',
            'java': '// YOUR CODE HERE',
            'javascript': '// YOUR CODE HERE\nthrow new Error("Not implemented");'
        })

        self.text_stub = self.params.get('text_stub', 'YOUR ANSWER HERE')
        self.begin_delimiter = self.params.get('begin_delimiter', 'BEGIN SOLUTION')
        self.end_delimiter = self.params.get('end_delimiter', 'END SOLUTION')
        self.enforce_metadata = self.params.get('enforce_metadata', True)

    def preprocess(self, nb: nbformat.NotebookNode, resources: Dict[str, Any]) -> Tuple[
        nbformat.NotebookNode, Dict[str, Any]]:
        language = nb.metadata.get('kernelspec', {}).get('language', 'python')

        if language not in self.code_stubs:
            self.log.warning(f"Language '{language}' not supported, using 'python' stub")
            language = 'python'

        resources['language'] = language

        for i, cell in enumerate(nb.cells):
            self._process_cell(cell, language, i)

        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']

        return nb, resources

    def _process_cell(self, cell: nbformat.NotebookNode, language: str, cell_index: int):
        if isinstance(cell.source, list):
            cell.source = ''.join(cell.source)
        elif not isinstance(cell.source, str):
            cell.source = str(cell.source)

        is_solution_cell = utils.is_solution(cell)

        has_solution_region = self._replace_solution_region(cell, language)

        if has_solution_region and not is_solution_cell and self.enforce_metadata:
            self.log.error(f"Cell {cell_index} has solution region but no solution metadata")
            raise ValueError(f"Solution region found in non-solution cell at index {cell_index}")

        if is_solution_cell and not has_solution_region:
            if cell.cell_type == 'code':
                cell.source = self.code_stubs[language]
            else:
                cell.source = self.text_stub

    def _replace_solution_region(self, cell: nbformat.NotebookNode, language: str) -> bool:
        lines = cell.source.split('\n')
        new_lines = []
        in_solution = False
        found_solution = False

        if cell.cell_type == 'code':
            stub_lines = self.code_stubs[language].split('\n')
        else:
            stub_lines = self.text_stub.split('\n')

        for line in lines:
            if self.begin_delimiter in line:
                if in_solution:
                    raise ValueError("Nested BEGIN SOLUTION found")

                in_solution = True
                found_solution = True

                indent = re.match(r'\s*', line).group(0)
                for stub_line in stub_lines:
                    new_lines.append(indent + stub_line)

            elif self.end_delimiter in line:
                if not in_solution:
                    raise ValueError("END SOLUTION without BEGIN SOLUTION")
                in_solution = False

            elif not in_solution:
                new_lines.append(line)

        if in_solution:
            raise ValueError("BEGIN SOLUTION without END SOLUTION")

        if found_solution:
            cell.source = '\n'.join(new_lines)

        return found_solution
