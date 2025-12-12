import logging
from abc import abstractmethod, ABC
import nbformat
from typing import Any, Dict, Optional, Tuple
from nbconvert.preprocessors import Preprocessor


class BaseProcessor(Preprocessor):

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kw):
        super().__init__(**kw)

        self.params = config or {}
        self.log = logging.getLogger(__name__)

    @abstractmethod
    def preprocess(self, nb: nbformat.NotebookNode, resources: Dict[str, Any]) -> Tuple[nbformat.NotebookNode, Dict[str, Any]]:
        pass


class ProcessorPipeline:

    def __init__(self, processors: list[BaseProcessor]):
        self.processors = processors
        self.log = logging.getLogger(__name__)

    def process(self, notebook: nbformat.NotebookNode, resources: Dict[str, Any]) -> Tuple[nbformat.NotebookNode, Dict[str, Any]]:
        self.log.debug(f"Running pipeline with {len(self.processors)} processors")

        for processor in self.processors:
            try:
                self.log.debug(f"Running {processor.__class__.__name__}")
                notebook, resources = processor.preprocess(notebook, resources)
            except Exception as e:
                self.log.error(f"Processor {processor.__class__.__name__} failed: {e}")
                raise

        return notebook, resources
