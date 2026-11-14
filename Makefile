all:
	docker-compose build
	docker-compose up

clean:
	docker-compose rm -vsf

distclean: clean
	docker volume rm -f artifactorial-data artifactorial-db

.PHONY: lint format test lock

lint:
	black --check .
	ruff check .

format:
	black .
	ruff check --fix .

test:
	pytest

# Re-pin requirements*.txt from requirements*.in (needs `pip install pip-tools`).
# Pass ARGS=--upgrade to move every pin to the newest allowed version.
lock:
	pip-compile -q --strip-extras --no-emit-index-url $(ARGS) --output-file requirements.txt requirements.in
	pip-compile -q --strip-extras --no-emit-index-url $(ARGS) --output-file requirements-dev.txt requirements-dev.in
