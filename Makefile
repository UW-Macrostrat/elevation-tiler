all:
	poetry run fastapi dev elevation_tiler

test:
	poetry run pytest