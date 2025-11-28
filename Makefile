# FastAPI 应用程序 Makefile
# =============================

# 变量
# =========

# 项目设置
APP_NAME := fastapi-app
PYTHON_VERSION := 3.12
ENVIRONMENT ?= dev

# 目录
SRC_DIR := app
TEST_DIR := test
SCRIPTS_DIR := scripts
CONF_DIR := conf
LOGS_DIR := logs

# 文件
REQUIREMENTS_FILE := pyproject.toml

# 命令
PYTHON := python3
PIP := pip
POETRY := poetry
UVICORN := $(POETRY) run uvicorn
PYTEST := $(POETRY) run pytest
BLACK := $(POETRY) run black
ISORT := $(POETRY) run isort
FLAKE8 := $(POETRY) run flake8
MYPY := $(POETRY) run mypy
DOCKER := docker
DOCKER_COMPOSE := docker-compose

# 默认目标
.DEFAULT_GOAL := help

# 目标
# =======

# 帮助
help:
	@echo "可用命令:"
	@echo "  setup        - 设置开发环境"
	@echo "  install      - 使用 Poetry 安装依赖"
	@echo "  update       - 更新依赖"
	@echo "  run          - 以开发模式运行应用程序"
	@echo "  run-prod     - 以生产模式运行应用程序"
	@echo "  test         - 运行测试"
	@echo "  test-cov     - 运行带覆盖率的测试"
	@echo "  lint         - 运行代码检查工具 (black, isort, flake8)"
	@echo "  typecheck    - 运行类型检查 (mypy)"
	@echo "  format       - 使用 black 和 isort 格式化代码"
	@echo "  clean        - 清理生成的文件"
	@echo "  init-db      - 初始化数据库"
	@echo "  build-docker - 构建 Docker 镜像"
	@echo "  run-docker   - 运行 Docker 容器"
	@echo "  help         - 显示此帮助信息"

# 设置开发环境
setup:
	@echo "正在设置开发环境..."
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install poetry
	@$(MAKE) install
	@mkdir -p $(LOGS_DIR)
	@echo "设置完成!"

# 安装依赖
install:
	@echo "正在安装依赖..."
	@$(POETRY) install
	@echo "依赖安装完成!"

# 更新依赖
update:
	@echo "正在更新依赖..."
	@$(POETRY) update
	@echo "依赖更新完成!"

# 以开发模式运行应用程序
run:
	@echo "以开发模式运行应用程序..."
	@$(POETRY) run python $(SCRIPTS_DIR)/start_app.py --env dev --reload

# 以生产模式运行应用程序
run-prod:
	@echo "以生产模式运行应用程序..."
	@$(POETRY) run python $(SCRIPTS_DIR)/start_app.py --env prod

# 运行测试
test:
	@echo "正在运行测试..."
	@$(PYTEST) $(TEST_DIR)

# 运行带覆盖率的测试
test-cov:
	@echo "正在运行带覆盖率的测试..."
	@$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html $(TEST_DIR)

# 运行代码检查工具
lint:
	@echo "正在运行代码检查工具..."
	@$(BLACK) --check $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	@$(ISORT) --check $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	@$(FLAKE8) $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	@echo "代码检查通过!"

# 运行类型检查
typecheck:
	@echo "正在运行类型检查..."
	@$(MYPY) $(SRC_DIR)
	@echo "类型检查通过!"

# 格式化代码
format:
	@echo "正在格式化代码..."
	@$(ISORT) $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	@$(BLACK) $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	@echo "代码格式化完成!"

# 清理生成的文件
clean:
	@echo "正在清理生成的文件..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -delete
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@rm -rf dist
	@rm -rf build
	@rm -rf *.log
	@echo "清理完成!"

# 初始化数据库
init-db:
	@echo "正在初始化数据库..."
	@$(POETRY) run python $(SCRIPTS_DIR)/init_db.py
	@echo "数据库初始化完成!"

# 构建 Docker 镜像
build-docker:
	@echo "正在构建 Docker 镜像..."
	@$(DOCKER) build -t $(APP_NAME):latest -f k8s/Dockerfile .
	@echo "Docker 镜像构建完成!"

# 运行 Docker 容器
run-docker:
	@echo "正在运行 Docker 容器..."
	@$(DOCKER) run -p 8000:8000 --env-file $(CONF_DIR)/$(ENVIRONMENT).env $(APP_NAME):latest

# 运行带 Shell 访问的 Docker 容器
run-docker-shell:
	@echo "正在运行带 Shell 访问的 Docker 容器..."
	@$(DOCKER) run -it --rm -p 8000:8000 --env-file $(CONF_DIR)/$(ENVIRONMENT).env $(APP_NAME):latest /bin/bash

# Docker Compose (如果使用 docker-compose.yml)
# docker-up:
# 	@echo "启动 Docker 容器..."
# 	@$(DOCKER_COMPOSE) up -d
# 
# docker-down:
# 	@echo "停止 Docker 容器..."
# 	@$(DOCKER_COMPOSE) down

# 数据库迁移 (如果使用 Alembic)
# migrate:
# 	@echo "正在运行数据库迁移..."
# 	@$(POETRY) run alembic upgrade head
# 
# migrate-create:
# 	@echo "正在创建新的迁移..."
# 	@$(POETRY) run alembic revision --autogenerate -m "$(name)"

# 生成 requirements.txt (用于遗留系统)
generate-requirements:
	@echo "正在生成 requirements.txt..."
	@$(POETRY) export -f requirements.txt --output requirements.txt --without-hashes
	@echo "requirements.txt 生成完成!"

# 检查安全漏洞
security-check:
	@echo "正在检查安全漏洞..."
	@$(POETRY) run pip-audit
	@echo "安全检查完成!"

# 发布流程
release:
	@echo "开始发布流程..."
	@$(MAKE) test
	@$(MAKE) lint
	@$(MAKE) typecheck
	@echo "发布检查通过!"

# CI/CD 辅助目标
ci:
	@echo "正在运行 CI 检查..."
	@$(MAKE) install
	@$(MAKE) lint
	@$(MAKE) typecheck
	@$(MAKE) test-cov
	@echo "CI 检查通过!"

# 伪目标 (非文件目标)
.PHONY: help setup install update run run-prod test test-cov lint typecheck format clean init-db build-docker run-docker run-docker-shell generate-requirements security-check release ci

# 错误处理
# =============

# 这将导致 Makefile 在任何错误时退出
.SHELLFLAGS := -ec

# 确保即使一个先决条件失败，所有先决条件都能构建
.DELETE_ON_ERROR:

# 包含任何本地覆盖
-include .env.mk