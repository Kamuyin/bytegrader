from __future__ import annotations

import asyncio
import logging
import shlex
from pathlib import Path
from typing import Iterable

import nbformat

from traitlets import Instance
from traitlets.config import Configurable

from bytegrader.autograde.executors.base import BaseExecutor

from .config import SystemdExecutorConfig
from .job_bundle import JobBundle
from .systemd_runner import (
    build_systemd_run_command,
    ensure_private_directory,
    launch_transient_unit,
    query_unit_state,
    render_environment_file,
)


class SystemdExecutor(BaseExecutor, Configurable):

    executor_config = Instance(SystemdExecutorConfig, allow_none=True)

    def __init__(self, **kwargs):
        config = kwargs.pop("systemd_executor_config", None)
        super().__init__(**kwargs)
        self.log = logging.getLogger("SystemdExecutor")
        self.executor_config = config or SystemdExecutorConfig(parent=self)

    async def execute_cell(self, cell_source, globals_dict=None):
        raise NotImplementedError("SystemdExecutor only supports notebook-level execution")

    async def execute_notebook(self, notebook: nbformat.NotebookNode, cell_ids: Iterable[str] | None = None):
        cfg = self.executor_config
        job_root = ensure_private_directory(Path(cfg.job_root))
        bundle = JobBundle.new(job_root, cfg.result_filename)
        bundle.initialise()

        metadata = {
            "cells": list(cell_ids) if cell_ids else None,
        }
        bundle.write_notebook(notebook, cell_ids)
        bundle.write_manifest(metadata)

        unit_name = cfg.unit_name_template.format(job_id=bundle.job_id)

        env_dir = ensure_private_directory(Path(cfg.runtime_directory_root))
        env_file = render_environment_file(
            env_dir,
            unit_name,
            {
                "BYTEGRADER_JOB_ID": bundle.job_id,
                "BYTEGRADER_BUNDLE": str(bundle.bundle_dir),
            },
        )

        exec_cmd = shlex.split(cfg.runner_entrypoint)
        exec_cmd.extend([str(bundle.bundle_dir), "--result", cfg.result_filename])

        properties = {
            "RuntimeDirectory": [bundle.job_id],
            "RuntimeDirectoryMode": "700",
            "RuntimeDirectoryPreserve": "no",
            "KillMode": "control-group",
        }

        workdir = Path(cfg.working_directory)
        workdir.mkdir(parents=True, exist_ok=True)

        command = build_systemd_run_command(
            unit_name=unit_name,
            exec_cmd=exec_cmd,
            workdir=workdir,
            properties=properties,
            env_file=env_file,
            slice_name=cfg.unit_slice or None,
        )

        self.log.debug("Launching systemd-run for %s", unit_name)
        return_code = await launch_transient_unit(command)
        if return_code != 0:
            self.log.error("systemd-run exited with code %s for %s", return_code, unit_name)

        final_state = await self._wait_for_completion(unit_name, timeout=cfg.start_timeout)

        results_payload = bundle.read_results() or {"cells": {}, "status": "missing"}
        results_payload.setdefault("metadata", {})
        results_payload["metadata"].update(
            {
                "unit_state": final_state,
                "systemd_return_code": return_code,
            }
        )

        manifest = bundle.read_manifest() or {}
        requested_cells = manifest.get("cells") or []

        cells_payload = results_payload.get("cells", {})
        if not isinstance(cells_payload, dict):
            cells_payload = {}
        cells = cells_payload
        if requested_cells:
            for cell_id in requested_cells:
                cells.setdefault(
                    cell_id,
                    {
                        "success": False,
                        "output": "",
                        "error": {
                            "message": "No output produced",
                            "detail": f"Cell {cell_id} missing from runner results",
                        },
                    },
                )

        failure_detected = (
            final_state in {"failed", "timeout"}
            or return_code != 0
            or results_payload.get("status") == "error"
        )

        if failure_detected:
            journal = await self._collect_journal(unit_name, cfg.journal_max_lines)
            results_payload["metadata"]["journal"] = journal
            for record in cells.values():
                if record.get("error") is None:
                    record["error"] = {"message": "Execution failed"}
                record.setdefault("success", False)

        if not cfg.preserve_job_artifacts:
            bundle.cleanup()

        return cells

    async def _wait_for_completion(self, unit_name: str, timeout: int) -> str:
        for _ in range(timeout):
            state = await query_unit_state(unit_name)
            if state in {"dead", "inactive", "failed"}:
                if state == "failed":
                    self.log.warning("Unit %s finished in failed state", unit_name)
                return state
            await asyncio.sleep(1)
        self.log.warning("Timeout waiting for unit %s to finish", unit_name)
        return "timeout"

    async def _collect_journal(self, unit_name: str, max_lines: int) -> str:
        from .systemd_runner import fetch_unit_logs

        try:
            journal = await fetch_unit_logs(unit_name, max_lines)
        except Exception as exc:
            self.log.error("Failed to collect journal for %s: %s", unit_name, exc)
            journal = ""
        return journal