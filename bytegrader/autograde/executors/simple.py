import logging
import traceback
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import nbformat
from traitlets.config import Configurable

from bytegrader.autograde.executors.base import BaseExecutor

# ! Only for demonstration purposes; must not be used in production due to security risks.
class SimpleExecutor(BaseExecutor, Configurable):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log = logging.getLogger("SimpleExecutor")
        self.log.info("SimpleExecutor initialized")

    async def execute_cell(self, cell_source, globals_dict=None):
        buf = StringIO()
        env = globals_dict if globals_dict is not None else {}

        try:
            self.log.info(f"Executing cell: {cell_source[:30]}...")
            with redirect_stdout(buf), redirect_stderr(buf):
                exec(cell_source, env)
            return {
                "success": True,
                "output": buf.getvalue(),
                "error": None
            }
        except Exception:
            return {
                "success": False,
                "output": buf.getvalue(),
                "error": {"traceback": traceback.format_exc()}
            }

    async def execute_notebook(self, notebook: nbformat.NotebookNode, cell_ids=None):
        nb_id = getattr(notebook, "metadata", {}).get("name", None)
        total = len(notebook.cells)
        self.log.info(f"Executing NotebookNode name={nb_id} with {total} cells")
        results = {}
        env = {}

        for cell in notebook.cells:
            cid = getattr(cell, "id", None)
            if cell.cell_type != "code":
                continue
            if cell_ids and cid not in cell_ids:
                continue
            res = await self.execute_cell(cell.source, globals_dict=env)
            results[cid] = res

        return results
