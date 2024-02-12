install:
	poetry install
build:
	poetry build
check:
	poetry run pytest -vv
	poetry run flake8 gendiff
PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app