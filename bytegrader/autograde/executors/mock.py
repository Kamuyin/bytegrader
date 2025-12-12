import logging

from traitlets import Unicode
from traitlets.config import Configurable

from bytegrader.autograde.executors.base import BaseExecutor


class MockExecutor(BaseExecutor, Configurable):

    bar = Unicode(
        "baz",
        help="Test"
    ).tag(config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log = logging.getLogger("MockExecutor")
        self.log.info(f"MockExecutor initialized with bar={self.bar}")

    async def execute_cell(self, cell_source, globals_dict=None):
        self.log.info(f"Mock executing cell: {cell_source[:30]}...")

        return {
            'success': True,
            'output': 'Mock output',
            'error': None
        }

    async def execute_notebook(self, notebook, cell_ids=None):
        self.log.info(f"Mock executing notebook with {len(notebook.cells)} cells")

        results = {}

        for cell in notebook.cells:
            cell_id = getattr(cell, 'id', None)
            if cell_ids and cell_id not in cell_ids:
                continue

            results[cell_id] = {
                'success': True,
                'output': 'Mock output',
                'error': None
            }

        return results
