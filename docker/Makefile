.SILENT:
.PHONY: build up down clean delete connect view network logs
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down
	docker rm -f $(docker ps -a -q)

clean: down
	docker rmi -f $(docker images -a -q)

delete: 
	docker volume rm $(docker volume ls -q)

connect:
	# Check if container name is provided as an argument
	if [ -z "${ARGS}" ]; then \
		echo "Usage: make connect ARGS=<container_name>"; \
		exit 1; \
	fi

	# Check if the container is running
	if ! docker inspect -f '{{.State.Running}}' "${ARGS}"; then \
		echo "Container '${ARGS}' is not running."; \
		exit 1; \
	fi

	# Connect to the container
	docker exec -it "${ARGS}" bash

view:
	docker ps

network:
	docker network ls

logs:
	docker-compose logs ${ARGS}