.PHONY: clean build install

# export PKG_MANAGER=uv && make install
PKG_MANAGER ?= $(shell command -v uv >/dev/null 2>&1 && echo "uv" || echo "pip")

# The only reason this file exists
clean:
	@echo "Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaning built labextension..."
	rm -rf bytegrader/labextension/ 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	@echo "Cleaning node modules..."
	rm -rf node_modules 2>/dev/null || true
	@echo "Cleaning lib directory..."
	rm -rf lib 2>/dev/null || true
	@echo "Cleaning TypeScript build artifacts..."
	rm -f tsconfig.tsbuildinfo 2>/dev/null || true
	@echo "Clean completed!"

build:
	@echo "Building bytegrader..."
	@echo "Using package manager: $(PKG_MANAGER)"
	@echo "Installing JavaScript dependencies..."
	jlpm install
	@echo "Building TypeScript and labextension..."
	jlpm build
	@echo "Building Python package..."
ifeq ($(PKG_MANAGER),uv)
	uv build
else
	python -m build
endif
	@echo "Build completed!"

install:
	@echo "Installing bytegrader with $(PKG_MANAGER)..."
ifeq ($(PKG_MANAGER),uv)
	uv pip install -e . --system --break-system-packages
else
	pip install -e .
endif
	@echo "Enabling Jupyter extensions..."
	jupyter server extension enable bytegrader --sys-prefix
	jupyter labextension develop . --overwrite
	@echo "Installation completed!"