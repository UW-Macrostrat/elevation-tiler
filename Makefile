all:
	poetry run fastapi dev elevation_tiler

test:
	poetry run pytest

build:
	# Get version from pyproject.toml
	docker build -t elevation-tiler:v$(shell poetry version -s) .
