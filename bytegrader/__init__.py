import json
from pathlib import Path
from typing import List, Dict

from .extensions.lab import load_jupyter_server_extension as load_lab_extension

__version__ = '0.0.1'

HERE = Path(__file__).parent.resolve()

if not (HERE / "extensions" / "labextension").exists():
    with (HERE / "extensions" / "labextension" / "package.json").open() as fid:
        data = json.load(fid)


    def _jupyter_labextension_paths():
        return [{
            "src": "labextension",
            "dest": data["name"]
        }]


def _jupyter_server_extension_points() -> List[Dict[str, str]]:
    return [{
        "module": "bytegrader",
    }]


def _load_jupyter_server_extension(app):
    load_lab_extension(app)


__all__ = [
    '__version__',
    '_jupyter_labextension_paths',
    '_jupyter_server_extension_points',
    '_load_jupyter_server_extension',
]