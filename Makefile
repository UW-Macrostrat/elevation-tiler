all:
	uv run fastapi dev elevation_tiler

test:
	uv run pytest

build:
	# Get version from pyproject.toml
	docker build -t elevation-tiler:v$(shell uv version --short) .
