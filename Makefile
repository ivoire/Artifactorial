all:
	docker-compose build
	docker-compose up 

clean:
	docker-compose rm -vsf

distclean: clean
	docker volume rm -f artifactorial-data artifactorial-db
