all:
	docker-compose build
	docker-compose up

clean:
	docker-compose rm -vsf

distclean: clean
	docker volume rm -f artifactorial-data artifactorial-db

.PHONY: lint format test

lint:
	black --check .
	ruff check .

format:
	black .
	ruff check --fix .

test:
	pytest
