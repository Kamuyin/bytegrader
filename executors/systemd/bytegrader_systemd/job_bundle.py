from __future__ import annotations

import copy
import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

import nbformat


@dataclass
class JobBundle:

    job_id: str
    root: Path
    result_filename: str

    bundle_dir: Path = field(init=False)
    notebook_path: Path = field(init=False)
    manifest_path: Path = field(init=False)
    result_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.bundle_dir = self.root / self.job_id
        self.notebook_path = self.bundle_dir / "submission.ipynb"
        self.manifest_path = self.bundle_dir / "manifest.json"
        self.result_path = self.bundle_dir / self.result_filename

    @staticmethod
    def new(job_root: Path, result_filename: str) -> "JobBundle":
        job_id = uuid.uuid4().hex
        return JobBundle(job_id=job_id, root=job_root, result_filename=result_filename)

    def initialise(self) -> None:
        self.bundle_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.bundle_dir, 0o755)

    def write_notebook(self, notebook: nbformat.NotebookNode, cell_ids: Iterable[str] | None = None) -> None:
        filtered = notebook
        if cell_ids:
            filtered = copy.deepcopy(notebook)
            filtered.cells = [cell for cell in filtered.cells if getattr(cell, "id", None) in cell_ids]
        nbformat.write(filtered, self.notebook_path)
        os.chmod(self.notebook_path, 0o644)

    def write_manifest(self, metadata: Mapping[str, object]) -> None:
        self.manifest_path.write_text(json.dumps(metadata), encoding="utf-8")
        os.chmod(self.manifest_path, 0o644)

    def prepare_result_file(self) -> None:
        self.result_path.write_text("{}", encoding="utf-8")
        os.chmod(self.result_path, 0o666)

    def read_manifest(self) -> Mapping[str, object] | None:
        if not self.manifest_path.exists():
            return None
        raw = self.manifest_path.read_text(encoding="utf-8")
        return json.loads(raw)

    def read_results(self) -> Mapping[str, object] | None:
        if not self.result_path.exists():
            return None
        raw = self.result_path.read_text(encoding="utf-8")
        return json.loads(raw)

    def cleanup(self) -> None:
        if self.bundle_dir.exists():
            import shutil

            shutil.rmtree(self.bundle_dir, ignore_errors=True)