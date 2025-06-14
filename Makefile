all:
	uv run fastapi dev --port 8005 elevation_tiler

test:
	uv run pytest

build:
	# Get version from pyproject.toml
	docker build -t elevation-tiler:v$(shell uv version --short) .

run-docker:
	make build
	docker run -p 8005:8000 --env-file .env -v data:/app/data elevation-tiler:v$(shell uv version --short)
