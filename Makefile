# Makefile — unified dev / test / prod targets
# Usage examples:
#   make help
#   make up-dev
#   make run-tests
#   make build-prod TAG=ci-123
#   make push-prod TAG=ci-123

SHELL := /bin/bash

# --- Configurable variables ---
COMPOSE_DEV    := docker-compose.dev_db.yml
COMPOSE_TEST   := docker-compose.test_db.yml
COMPOSE_PROD   := docker-compose.yml
DOCKER_COMPOSE := $(shell command -v docker-compose >/dev/null 2>&1 && echo docker-compose || echo "docker compose")

DOCKERFILE        := Dockerfile
DOCKERFILE_DEV    := Dockerfile.dev
DOCKERFILE_TEST   := Dockerfile.test

TARGET_DEV  := dev
TARGET_TEST := test
TARGET     := prod

# service name for exec/migrate
SERVICE := app
DB_SERVICE := db

# DB User
DB_USER := flask_user
DB_NAME := flask_db

# Image / registry settings (override via env or make VAR=value)
IMAGE_NAME := flask-devops-portfolio
REGISTRY   := ghcr.io/your-org
TAG        := latest

# script(s) in repo (used if present)
RUN_TESTS_SCRIPT := ./run-tests.sh

# --- Phony ---
.PHONY: help dev test prod build-dev compose-build-dev up-dev up-build-dev up-nobuild-dev down-dev restart-dev logs-dev ps-dev exec-dev shell-dev clean-dev\
        build-test up-test down-test restart-test logs-test ps-test run-tests clean-test run-demo-test run-test-only\
        build-prod push-prod compose-build-prod up-build-prod up-nobuild-prod up-prod down-prod restart-prod logs-prod ps-prod \
        migrate migrate-dev db-shell prune
		lint test

# --- Help ---
help:
	@echo "Makefile commands:"
	@echo ""
	@echo "  dev (local dev & DB)"
	@echo "    make build-dev     			# build dev stack"
	@echo "	   make compose-build-dev 		# build dev stack via docker-compose"
	@echo "    make up-dev        			# start dev stack"
	@echo "    make up-build-dev  			# start dev stack (build first)"
	@echo "    make up-nobuild-dev			# start dev stack (no build)"
	@echo "    make down-dev      			# stop dev stack"
	@echo "    make restart-dev   			# restart dev stack"
	@echo "    make logs-dev      			# tail dev logs"
	@echo "    make ps-dev        			# list dev services"
	@echo "    make exec-dev CMD='<shell or command>'   # run command in dev $(SERVICE) container"
	@echo "    make shell-dev     			# Open shell terminal in Dev $(SERVICE) container"
	@echo "    make clean-dev     			# stop dev stack and remove volumes"
	@echo ""
	@echo "  test"
	@echo "    make build-test    			# build test stack"
	@echo "    make up-test       			# start test stack"
	@echo "    make down-test     			# stop test stack"
	@echo "    make logs-test     			# tail test logs"
	@echo "    make clean-test   			# stop test stack and remove volumes"
	@echo "    make run-tests    			# run tests (prefers ./run-tests.sh if present)"
	@echo "    make build-test    			# build test image (Dockerfile.test)"
	@echo "    make run-demo-test     		# start postgres, recreate DB and run tests in transient container"
	@echo "    make run-test-only     		# run only tests once in transient container"
	@echo ""
	@echo "  prod"
	@echo "    make build-prod TAG=<tag>    # build prod image (Dockerfile)"
	@echo "    make push-prod TAG=<tag>     # tag & push to REGISTRY"
	@echo "	   make compose-build-prod 		# build prod stack via docker-compose"
	@echo "    make up-prod       			# start prod stack"
	@echo "    make up-build-prod  			# start prod stack (build first)"
	@echo "    make up-nobuild-prod			# start prod stack (no build)"
	@echo "    make down-prod               # stop prod stack"
	@echo "    make restart-prod            # restart prod stack"
	@echo "    make logs-prod               # tail prod logs"
	@echo ""
	@echo "  misc"
	@echo "    make migrate                 # run alembic upgrade head on $(SERVICE) (uses docker-compose.dev_db.yml)"
	@echo "    make db-shell                # Open DB shell in Dev $(DB_SERVICE) container"
	@echo "    make prune                   # docker system prune -f (careful!)"

# -------------------------
# Build images
# -------------------------
build-dev:
	@echo "[make] Building dev image using $(DOCKERFILE_DEV)"
	docker build --no-cache --target $(TARGET_DEV) -t $(IMAGE_NAME):dev -f $(DOCKERFILE_DEV) .

build-test:
	@echo "[make] Building test image using $(DOCKERFILE_TEST)"
	docker build --no-cache --target $(TARGET_TEST) -t $(IMAGE_NAME):test -f $(DOCKERFILE_TEST) .

build-prod:
	@echo "[make] Building prod image using Dockerfile=$(DOCKERFILE) target=$(TARGET)"
	docker build --no-cache --target $(TARGET) -t $(IMAGE_NAME):$(TAG) -f $(DOCKERFILE) .

# -------------------------
# Compose build / up flows
# -------------------------
#----------DEV TARGETS----------
compose-build-dev:
	@echo "[make] Starting dev stack from $(COMPOSE_DEV)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) build

up-dev:
	@echo "[make] Starting dev stack from $(COMPOSE_DEV)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) up -d

up-dev-build:
	@echo "[make] Starting dev stack (build) from $(COMPOSE_DEV)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) up -d --build

up-dev-nobuild:
	@echo "[make] Starting dev stack (no build) from $(COMPOSE_DEV)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) up -d --no-build

down-dev:
	@echo "[make] Stopping dev stack"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) down

restart-dev:
	@echo "[make] Restarting dev stack"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) restart

logs-dev:
	@echo "[make] Tailing dev logs (ctrl-c to exit)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) logs -f

ps-dev:
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) ps

exec-dev:
	@if [ -z "$(SERVICE)" ]; then \
	  echo "Usage: make exec-dev SERVICE=<service> CMD='<command>'"; exit 2; \
	fi
	@if [ -z "$(CMD)" ]; then \
	  echo "Usage: make exec-dev SERVICE=<service> CMD='<command>'"; exit 2; \
	fi
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) exec $(SERVICE) /bin/sh -c "$(CMD)"

shell-dev:
	@if [ -z "$(SERVICE)" ]; then \
	  echo "Usage: make shell-dev SERVICE=<service>"; exit 2; \
	fi
	@echo "[make] Entering shell in DEV container: $(SERVICE)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) exec $(SERVICE) /bin/sh

#----------TEST TARGETS----------
up-test:
	@echo "[make] Starting test stack from $(COMPOSE_TEST)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) up -d

down-test:
	@echo "[make] Stopping test stack"
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) down

restart-test:
	@echo "[make] Restarting test stack"
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) restart

logs-test:
	@echo "[make] Tailing test logs (ctrl-c to exit)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) logs -f

ps-test:
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) ps

clean-test:
	@echo "[make] Cleaning: stopping test stacks and removing volumes"
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) down --volumes --remove-orphans || true


# Prefer ./run-tests.sh if present (keeps CI script parity); otherwise run pytest locally
run-tests:
	@if [ -x "$(RUN_TESTS_SCRIPT)" ]; then \
	  echo "[make] Running tests via $(RUN_TESTS_SCRIPT)"; $(RUN_TESTS_SCRIPT); \
	else \
	  echo "[make] Running pytest locally"; pytest -v; \
	fi

run-demo-test:
	@echo ">>> Demo: recreate DB, start postgres, run tests in transient container"
	@printf "Using compose file: %s\n" "$(COMPOSE_TEST)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) down -v --remove-orphans || true
	# start only DB service so the test run container can be fast
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) up -d $(DB_SERVICE)
	# run tests in a throwaway container that runs run-tests.sh (reads .env.dev)
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) run --rm $(SERVICE) ./ci/run-tests.sh

run-test-only:
	@echo ">>> Test: run only tests once in transient container"
	@printf "Using compose file: %s\n" "$(COMPOSE_TEST)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_TEST) run --rm $(SERVICE) ./ci/run-tests.sh

#----------PROD TARGETS----------

compose-build-prod:
	@echo "[make] Starting dev stack from $(COMPOSE_PROD)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD) build

up-prod:
	@echo "[make] Starting dev stack from $(COMPOSE_PROD)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD) up -d

up-build-prod:
	@echo "[make] Starting dev stack (build) from $(COMPOSE_PROD)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD) up -d --build

up-nobuild-prod:
	@echo "[make] Starting dev stack (no build) from $(COMPOSE_PROD)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD) up -d --no-build

down-prod:
	@echo "[make] Stopping prod compose"
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD) down

restart-prod:
	@echo "[make] Restarting prod compose"
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD) restart

logs-prod:
	@echo "[make] Tailing prod logs (ctrl-c to exit)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD) logs -f

ps-prod:
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD) ps

shell-prod:
	@echo "[make] Enter into shell in DEV contianer"
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD) exec $(SERVICE) /bin/sh

	
# -------------------------
# Migrations (uses dev compose by default)
# -------------------------
# This runs alembic inside the configured service. Override SERVICE if needed.
migrate:
	@echo "[make] Running alembic upgrade head on service '$(SERVICE)' using $(COMPOSE_DEV)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) exec -T $(SERVICE) alembic upgrade head

db-shell:
	@echo "[make] Running DB shell on '$(SERVICE)' using $(COMPOSE_DEV)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) exec $(DB_SERVICE) psql -U $(DB_USER) -d $(DB_NAME)

prune:
	@read -p "This will run 'docker system prune -a --volumes'. Continue? (y/N) " ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
	  docker system prune -a --volumes -f; \
	else \
	  echo "Aborted."; \
	fi

clean-dev:
	@echo "[make] Cleaning: stopping dev stacks and removing volumes"
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV) down --volumes --remove-orphans || true

push-prod:
	@if [ -z "$(TAG)" ]; then echo "Usage: make push-prod TAG=<tag>"; exit 1; fi
	@IMAGE_TAG=$(REGISTRY)/$(IMAGE_NAME):$(TAG); \
	echo "[make] Tagging $(IMAGE_NAME):$(TAG) -> $${IMAGE_TAG}"; \
	docker tag $(IMAGE_NAME):$(TAG) $${IMAGE_TAG}; \
	echo "[make] Pushing $${IMAGE_TAG}"; \
	docker push $${IMAGE_TAG}

# -------------------------
# Simple dev QA tasks
# -------------------------
lint:
	@echo "[make] Running lint (flake8)"
	# adjust as needed; do not fail the make if flake8 not installed locally
	@if command -v flake8 >/dev/null 2>&1; then flake8 . || true; else echo "flake8 not found, skipping"; fi

test:
	@echo "[make] Running pytest"
	@if command -v pytest >/dev/null 2>&1; then pytest -q; else echo "pytest not found, skipping"; fi
