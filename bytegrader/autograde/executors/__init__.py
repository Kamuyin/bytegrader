# from .simple import SimpleExecutor

# __all__ = ["SimpleExecutor"]
_all__ = []

try:
    from .wasm import WasmExecutor
    __all__.append("WasmExecutor")
except ImportError:
    pass
