import os
import tempfile
import logging
import traceback
from wasmtime import Config, Engine, Linker, Module, Store, WasiConfig
from traitlets import Unicode, Integer
from traitlets.config import Configurable
import nbformat
import json

from bytegrader.autograde.executors.base import BaseExecutor


class WasmExecutor(BaseExecutor, Configurable):
    wasm_path = Unicode(
        "",
        help="Path to the Python WASM module.",
        allow_none=False
    ).tag(config=True)

    stdlib_path = Unicode(
        "",
        help="Path to the Python stdlib WASM module.",
        allow_none=False
    ).tag(config=True)

    memory_limit = Integer(
        1 << 28,  # 256MB
        help="Memory limit for the WASM execution in bytes."
    ).tag(config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log = logging.getLogger("WasmExecutor")

        if not os.path.exists(self.wasm_path):
            raise FileNotFoundError(f"WASM module not found at {self.wasm_path}")
        if not os.path.exists(self.stdlib_path):
            raise FileNotFoundError(f"Python standard library not found at {self.stdlib_path}")
        if self.memory_limit <= 0:
            raise ValueError("Memory limit must be positive")

    async def execute_cell(self, cell_source, globals_dict=None):
        pass

    async def execute_notebook(self, notebook: nbformat.NotebookNode, cell_ids=None):
        nb_id = "Unknown"
        self.log.info(f"Executing NotebookNode name={nb_id} with {len(notebook.cells)} cells")

        script = self._generate_script(notebook, cell_ids)

        results = self._run(script)
        if results is None:
            self.log.error("WASM execution failed")
            return None

        cell_results = {}
        code_cells = [c for c in notebook.cells if c.cell_type == "code"]
        print(f"Code cells: {code_cells}")
        for cell, res in zip(code_cells, results):
            cid = cell.id
            if cell_ids and cid not in cell_ids:
                continue
            cell_results[cid] = {
                "success": res["success"],
                "output": res["output"],
                "error": res["error"]
            }

        return cell_results

    # ! TODO: Make it safer against injection attacks :-P
    def _generate_script(self, notebook, cell_ids):
        cells = [c.source for c in notebook.cells if c.cell_type == "code"]
        if cell_ids:
            cells = [c.source for c in notebook.cells if c.cell_type == "code" and c.id in cell_ids]

        script = """
import sys
import traceback
import json

cells = {}

results = []
for i, cell in enumerate(cells):
    print(f'START_CELL_{{i}}')
    try:
        exec(cell)
        success = True
        error = None
    except Exception as e:
        success = False
        error = traceback.format_exc()
    print(f'END_CELL_{{i}}')
    results.append({{
        'success': success,
        'error': error,
        'output': ''
    }})

print('---RESULTS---')
print(json.dumps(results))
print('---END_RESULTS---')
""".format(repr(cells))

        return script

    def _run(self, script):
        engine_cfg = Config()
        engine_cfg.static_memory_maximum_size = self.memory_limit
        linker = Linker(Engine(engine_cfg))
        linker.define_wasi()

        if not os.path.exists(self.wasm_path):
            raise FileNotFoundError(f"WASM module not found at {self.wasm_path}")
        python_module = Module.from_file(linker.engine, self.wasm_path)

        config = WasiConfig()
        config.argv = ("python", "-c", script)

        if not os.path.exists(self.stdlib_path):
            raise FileNotFoundError(f"Python stdlib not found at {self.stdlib_path}")
        config.preopen_dir(self.stdlib_path, "/usr/local/lib/python3.11")

        with tempfile.TemporaryDirectory() as chroot:
            out_log = os.path.join(chroot, "out.log")
            err_log = os.path.join(chroot, "err.log")
            config.stdout_file = out_log
            config.stderr_file = err_log
            config.preopen_dir(chroot, chroot)

            store = Store(linker.engine)
            store.set_wasi(config)

            try:
                instance = linker.instantiate(store, python_module)
                start = instance.exports(store)["_start"]
                start(store)

                with open(out_log) as f:
                    output = f.read()

                results_json = ""
                in_results = False
                outputs = {}
                current_output = []
                current_cell = None
                for line in output.splitlines():
                    if line == "---RESULTS---":
                        in_results = True
                        continue
                    elif line == "---END_RESULTS---":
                        in_results = False
                        continue
                    elif in_results:
                        results_json += line
                        continue
                    if line.startswith("START_CELL_"):
                        current_cell = int(line.split('_')[2])
                        current_output = []
                    elif line.startswith("END_CELL_"):
                        if current_cell is not None:
                            outputs[current_cell] = "\n".join(current_output)
                            current_cell = None
                    else:
                        if current_cell is not None:
                            current_output.append(line)

                results = json.loads(results_json)

                for i, res in enumerate(results):
                    res["output"] = outputs.get(i, "")

                return results
            except Exception as e:
                with open(err_log) as f:
                    error = f.read()
                self.log.error(f"WASM execution error: {e}\nStderr: {error}")
                return None
