.PHONY: help install dev build test demo docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install     Install backend and frontend dependencies"
	@echo "  make dev         Run backend server (FastAPI) on port 8000"
	@echo "  make build       Build frontend production bundle"
	@echo "  make test        Run unit test suite"
	@echo "  make demo        Generate real 1-minute sample podcast episodes in English and Hindi"
	@echo "  make docker-up   Start application via Docker Compose"
	@echo "  make docker-down Stop Docker Compose application"

install:
	pip install -r requirements.txt
	cd frontend && npm install

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

build:
	cd frontend && npm run build

test:
	python -m pytest tests/ -v

demo:
	python -m app.demo --lang all

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

