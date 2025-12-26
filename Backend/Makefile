install: pyproject.toml poetry.toml
	pip install -e '.'
	cp skel/.env.skel .env

install-dev: pyproject.toml poetry.toml skel/
	pip install -e '.[test, dev]'
	cp skel/.env.skel .env

run: .env
	python app/main.py

run-db: .env compose.yaml
	docker compose up postgresql

test: tests
	pytest tests --cov
	coverage html