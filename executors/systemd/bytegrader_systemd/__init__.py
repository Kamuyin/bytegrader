from importlib import import_module

__all__ = ["SystemdExecutor", "SystemdExecutorConfig"]


def __getattr__(name: str):
	if name == "SystemdExecutor":
		return import_module(".executor", __name__).SystemdExecutor
	if name == "SystemdExecutorConfig":
		return import_module(".config", __name__).SystemdExecutorConfig
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")