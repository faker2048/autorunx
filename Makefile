.PHONY: help install test lint format clean dev demo

# 默认目标
help: ## Show help information
	@echo "Autostartx development commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies
	uv pip install -e ".[dev]"

test: ## Run tests
	PYTHONPATH=src pytest tests/ -v

test-cov: ## Run tests and generate coverage report
	PYTHONPATH=src pytest tests/ --cov=autostartx --cov-report=html --cov-report=term

lint: ## Run code checks
	ruff check src/ tests/
	mypy src/autostartx

format: ## Format code
	black src/ tests/
	ruff check --fix src/ tests/

clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/

dev: ## Run in development mode
	PYTHONPATH=src python -c "from autostartx.cli import main; main()"

demo: ## Run demo examples
	python examples/basic_usage.py

build: ## Build package
	python -m build

install-local: ## Local installation
	uv pip install click psutil rich toml
	@echo "Dependencies installed, you can run with PYTHONPATH=src python -c \"from autostartx.cli import main; main()\""

install-github: ## Install from GitHub (for testing)
	pip install git+https://github.com/faker2048/autostartx.git
	@echo "Installed from GitHub, you can use the autostartx command directly"

test-uvx: ## Test running uvx from GitHub
	@echo "Test running uvx from GitHub:"
	@echo "uvx --from git+https://github.com/faker2048/autostartx autostartx --help"

# Quick commands
add: ## Add service (usage: make add CMD="command" NAME="name")
	PYTHONPATH=src python -c "from autostartx.cli import main; main()" add "$(CMD)" --name "$(NAME)"

list: ## View service list
	PYTHONPATH=src python -c "from autostartx.cli import main; main()" list

status: ## View service status (usage: make status NAME="name")
	PYTHONPATH=src python -c "from autostartx.cli import main; main()" status --name "$(NAME)"