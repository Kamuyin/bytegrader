from typing import Dict, Any, List, Tuple
from .base import BaseProcessor, ProcessorPipeline
import nbformat

from .transform import ClearHiddenTestsProcessor
from .transform.clear_markingscheme import ClearMarkSchemeProcessor
from .transform.clear_solutions import ClearSolutionsProcessor
from .transform.lockcells import LockCellsProcessor


class ProcessorFactory:
    PROCESSORS = {
        'clear_solutions': ClearSolutionsProcessor,
        'lock_cells': LockCellsProcessor,
        'clear_hidden_tests': ClearHiddenTestsProcessor,
        'clear_markingscheme': ClearMarkSchemeProcessor
    }

    @classmethod
    def create_processor(cls, processor_name: str, config: Dict[str, Any] = None, logger=None) -> BaseProcessor:
        if processor_name not in cls.PROCESSORS:
            raise ValueError(f"Unknown processor: {processor_name}. Available: {list(cls.PROCESSORS.keys())}")

        processor_class = cls.PROCESSORS[processor_name]
        return processor_class(config=config, logger=logger)

    @classmethod
    def create_pipeline(cls, processor_configs: List[Dict[str, Any]]) -> ProcessorPipeline:
        processors = []

        for proc_config in processor_configs:
            proc_name = proc_config['name']
            proc_specific_config = proc_config.get('config', {})

            processor = cls.create_processor(proc_name, proc_specific_config)
            processors.append(processor)

        return ProcessorPipeline(processors)

    @classmethod
    def create_assignment_generation_pipeline(cls, config: Dict[str, Any] = None) -> ProcessorPipeline:
        pipeline_config = [
            {'name': 'lock_cells', 'config': config.get('lock_cells', {}) if config else {}},
            {'name': 'clear_solutions', 'config': config.get('clear_solutions', {}) if config else {}},
            {'name': 'clear_hidden_tests', 'config': config.get('clear_hidden_tests', {}) if config else {}},
            {'name': 'clear_markingscheme', 'config': config.get('clear_markingscheme', {}) if config else {}}
        ]

        return cls.create_pipeline(pipeline_config)

    @classmethod
    def preprocess_notebook(cls, notebook: nbformat.NotebookNode,
                            processor_configs: List[Dict[str, Any]],
                            resources: Dict[str, Any] = None,
                            logger=None) -> Tuple[nbformat.NotebookNode, Dict[str, Any]]:
        if resources is None:
            resources = {}

        pipeline = cls.create_pipeline(processor_configs, logger)
        return pipeline.process(notebook, resources)
