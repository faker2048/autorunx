.PHONY: help install test lint format clean dev demo

# 默认目标
help: ## 显示帮助信息
	@echo "AutoRunX 开发命令："
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 安装开发依赖
	uv pip install -e ".[dev]"

test: ## 运行测试
	PYTHONPATH=src pytest tests/ -v

test-cov: ## 运行测试并生成覆盖率报告
	PYTHONPATH=src pytest tests/ --cov=autorunx --cov-report=html --cov-report=term

lint: ## 运行代码检查
	ruff check src/ tests/
	mypy src/autorunx

format: ## 格式化代码
	black src/ tests/
	ruff check --fix src/ tests/

clean: ## 清理临时文件
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/

dev: ## 开发模式运行
	PYTHONPATH=src python -c "from autorunx.cli import main; main()"

demo: ## 运行演示示例
	python examples/basic_usage.py

build: ## 构建包
	python -m build

install-local: ## 本地安装
	uv pip install click psutil rich toml
	@echo "已安装依赖，可以使用 PYTHONPATH=src python -c \"from autorunx.cli import main; main()\" 运行"

# 快捷命令
add: ## 添加服务（使用方法：make add CMD="command" NAME="name"）
	PYTHONPATH=src python -c "from autorunx.cli import main; main()" add "$(CMD)" --name "$(NAME)"

list: ## 查看服务列表
	PYTHONPATH=src python -c "from autorunx.cli import main; main()" list

status: ## 查看服务状态（使用方法：make status NAME="name"）
	PYTHONPATH=src python -c "from autorunx.cli import main; main()" status --name "$(NAME)"