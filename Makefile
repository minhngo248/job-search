.PHONY: help install-infrastructure install-backend install-frontend install test-backend test-frontend test lint-backend format-backend clean

help:
	@echo "Available commands:"
	@echo "  install                 - Install all dependencies"
	@echo "  install-infrastructure  - Install CDK dependencies"
	@echo "  install-backend        - Install backend dependencies"
	@echo "  install-frontend       - Install frontend dependencies"
	@echo "  test                   - Run all tests"
	@echo "  test-backend           - Run backend tests"
	@echo "  test-frontend          - Run frontend tests"
	@echo "  lint-backend           - Run backend linting"
	@echo "  format-backend         - Format backend code"
	@echo "  clean                  - Clean build artifacts"

install: install-infrastructure install-backend install-frontend

install-infrastructure:
	cd infrastructure && python -m venv .venv && \
	. .venv/bin/activate && \
	pip install -r requirements.txt

install-backend:
	cd backend && python -m venv .venv && \
	. .venv/bin/activate && \
	pip install -r requirements.txt && \
	pip install -r requirements-dev.txt

install-frontend:
	cd frontend && npm install

test: test-backend test-frontend

test-backend:
	cd backend && . .venv/bin/activate && pytest

test-frontend:
	cd frontend && npm test -- --run

lint-backend:
	cd backend && . .venv/bin/activate && \
	flake8 src tests && \
	mypy src

format-backend:
	cd backend && . .venv/bin/activate && \
	black src tests

clean:
	rm -rf infrastructure/.venv infrastructure/cdk.out infrastructure/.cdk.staging
	rm -rf backend/.venv backend/build backend/dist backend/*.egg-info
	rm -rf backend/__pycache__ backend/.pytest_cache backend/.mypy_cache
	rm -rf frontend/node_modules frontend/dist
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete