from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import nbformat

try:
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError
except ImportError:
    NotebookClient = None
    CellExecutionError = Exception


def run_notebook(bundle_dir: Path, result_filename: str) -> dict[str, Any]:

    notebook_path = bundle_dir / "submission.ipynb"
    result_path = bundle_dir / result_filename
    if NotebookClient is None:
        raise RuntimeError("nbclient is unavailable in the runner environment")

    nb = nbformat.read(notebook_path, as_version=nbformat.NO_CONVERT)
    kernel_name = nb.metadata.get("kernelspec", {}).get("name") if isinstance(nb.metadata, dict) else None
    client = NotebookClient(
        nb,
        timeout=600,
        resources={"metadata": {"path": str(bundle_dir)}},
        allow_errors=True,
        kernel_name=kernel_name,
    )

    status = "ok"
    error_info: dict[str, Any] | None = None

    try:
        executed = client.execute()
    except CellExecutionError as exc:
        executed = exc.working_notebook
        status = "error"
        error_info = {"message": str(exc)}
    except Exception as exc:
        executed = nb
        status = "error"
        error_info = {"message": str(exc)}

    cell_results: dict[str, Any] = {}
    for cell in executed.cells:
        cell_id = getattr(cell, "id", None)
        if cell_id is None or cell.cell_type != "code":
            continue

        flat_outputs: list[str] = []
        error_output: dict[str, Any] | None = None
        for output in cell.get("outputs", []):
            otype = output.get("output_type")
            if otype == "stream":
                flat_outputs.append(output.get("text", ""))
            elif otype in {"execute_result", "display_data"}:
                data = output.get("data", {})
                if isinstance(data, dict):
                    text = data.get("text/plain")
                    if isinstance(text, list):
                        flat_outputs.append("".join(text))
                    elif isinstance(text, str):
                        flat_outputs.append(text)
            elif otype == "error":
                traceback = output.get("traceback")
                if isinstance(traceback, list):
                    trace_text = "\n".join(traceback)
                else:
                    trace_text = str(traceback or "")
                error_output = {
                    "ename": output.get("ename"),
                    "evalue": output.get("evalue"),
                    "traceback": trace_text,
                }

        cell_results[cell_id] = {
            "success": error_output is None,
            "output": "".join(flat_outputs),
            "error": error_output,
        }

    payload = {
        "cells": cell_results,
        "status": status,
        "error": error_info,
    }
    result_path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BYTEGrader systemd runner")
    parser.add_argument("bundle", type=Path, help="Path to the prepared job bundle")
    parser.add_argument("--result", default="results.json", help="Relative filename for result JSON")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    result_path = args.bundle / args.result
    try:
        run_notebook(args.bundle, args.result)
    except Exception as exc:
        logging.exception("Runner failed with unhandled exception")
        try:
            result_path.write_text(
                json.dumps({"cells": {}, "status": "error", "error": {"message": str(exc)}}),
                encoding="utf-8",
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()