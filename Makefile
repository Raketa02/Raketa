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


# Run all tests
# Example: make test
test-container:
	docker exec -it $$(docker ps --filter "name=_api" --format "{{.Names}}" | head -n 1) python -m pytest /home/docker_user/app/application/$(TEST)
# Example (file): make test-file FILE=tests/test_user.py
# Example (function): make test-function TEST=tests/test_user.py::test_create_user
# Example (funciton in a test class) make test-function TEST=tests/test_user.py::TestUser::test_create_user
test-file:
	poetry run pytest $(FILE)


