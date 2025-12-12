from abc import abstractmethod

from nbformat import NotebookNode
from traitlets.config import LoggingConfigurable


class BaseExecutor(LoggingConfigurable):

    @abstractmethod
    async def execute_cell(self, cell_source, globals_dict=None):
        pass

    @abstractmethod
    async def execute_notebook(self, notebook: NotebookNode, cell_ids=None):
        pass
