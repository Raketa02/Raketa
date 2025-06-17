COMPOSE_DEV=docker-compose -f docker-compose-dev.yml
STACK_NAME=basebackend
SECRETS_DIR=.secrets
IMAGE_NAME=robertconstantin02/basebackend_api:dev

.PHONY: help build push init-swarm create-secrets deploy up down logs ps

help:
	@echo "Available commands:"
	@echo "  build             Build Docker image"
	@echo "  push              Push image to Docker Hub"
	@echo "  init-swarm        Initialize Docker Swarm"
	@echo "  create-secrets    Create/update Swarm secrets"
	@echo "  deploy            Deploy stack using Docker Swarm"
	@echo "  up                Shorthand for build + deploy"
	@echo "  down              Remove stack"
	@echo "  logs              Show logs"
	@echo "  ps                List running containers"

build:
	docker build -t $(IMAGE_NAME) -f docker/api/Dockerfile.dev .

push:
	docker push $(IMAGE_NAME)

init-swarm:
	docker swarm init || true

create-secrets:
	docker secret rm postgres_password || true
	docker secret create postgres_password $(SECRETS_DIR)/postgres_password.txt

deploy: create-secrets
	docker stack deploy -c docker-compose-dev.yml $(STACK_NAME)

up: build push deploy

down:
	docker stack rm $(STACK_NAME)

logs:
	docker service logs $(STACK_NAME)_api

ps:
	docker stack ps $(STACK_NAME)


run-postgres-manual:
	docker rm -f my-postgres-ssl || true
	docker run --name my-postgres-ssl \
		-e POSTGRES_USER=basebackend_user \
		-e POSTGRES_DB=basebackendb \
		-e POSTGRES_PASSWORD=mysecretpassword \
		-v $$(pwd)/.secrets/server.crt:/var/lib/postgresql/server.crt:ro \
		-v $$(pwd)/.secrets/server.key:/var/lib/postgresql/server.key:ro \
		-v $$(pwd)/.secrets/rootCA.crt:/var/lib/postgresql/rootCA.crt:ro \
		-v $$(pwd)/pgdata:/var/lib/postgresql/data \
		-v $$(pwd)/docker/postgres/config/postgresql.conf:/etc/postgresql/postgresql.conf \
		-v $$(pwd)/docker/postgres/config/pg_hba.conf:/etc/postgresql/pg_hba.conf \
		-p 5432:5432 \
		-d postgres:17 \
		-c config_file=/etc/postgresql/postgresql.conf \
		-c hba_file=/etc/postgresql/pg_hba.conf
