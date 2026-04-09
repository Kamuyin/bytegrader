from abc import abstractmethod

from nbformat import NotebookNode
from traitlets import Integer
from traitlets.config import LoggingConfigurable


class BaseExecutor(LoggingConfigurable):

    execution_timeout = Integer(
        300,
        help=(
            "Maximum seconds allowed for a single notebook execution."
            "Set to 0 to disable the timeout."
        ),
    ).tag(config=True)

    @abstractmethod
    async def execute_cell(self, cell_source, globals_dict=None):
        pass

    @abstractmethod
    async def execute_notebook(self, notebook: NotebookNode, cell_ids=None):
        pass

    async def cleanup(self) -> None:
        """Called by the worker after execute_notebook completes or is cancelled."""
        pass