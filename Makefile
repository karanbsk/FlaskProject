# Variables
COMPOSE = docker-compose -p flask_dev -f docker-compose.dev_db.yml
FLASK_APP = flask_web
DB_SERVICE = db
DB_USER = flask_user
DB_NAME = flask_db

#  Docker Container Management
containers-up:
	$(COMPOSE) up -d

container-up:
	$(COMPOSE) up -d $(SERVICE)


containers-down:
	$(COMPOSE) down

container-down:
	$(COMPOSE) down -d $(SERVICE)

containers-logs:
	$(COMPOSE) logs -f

containers-ps:
	$(COMPOSE) ps

containers-restart:
	$(COMPOSE) restart

container-restart:
	$(COMPOSE) restart $(SERVICE) 

#  Database Management
db-shell:
	$(COMPOSE) exec $(DB_SERVICE) psql -U $(DB_USER) -d $(DB_NAME)

db-migrate-up:
	$(COMPOSE) run --rm $(FLASK_APP) flask db upgrade

db-migrate-down:
	$(COMPOSE) run --rm $(FLASK_APP) flask db downgrade -1

db-migrate-revision:
	$(COMPOSE) run --rm $(FLASK_APP) flask db revision --autogenerate -m "manual migration"

#  Flask App Helpers
app-shell:
	$(COMPOSE) exec $(FLASK_APP) flask shell

app-test:
	$(COMPOSE) run --rm $(FLASK_APP) pytest -v

help:
	@echo "Available commands:"
	@echo "  containers-up           Start all containers"
	@echo "  containers-down         Stop all containers"
	@echo "  containers-logs         Tail logs"
	@echo "  container-up SERVICE=X  Start single container"
	@echo "  container-restart SERVICE=X  Restart single container"
	@echo "  db-shell                Open Postgres shell"
	@echo "  db-migrate-up           Apply migrations"
	@echo "  db-migrate-down         Rollback last migration"
	@echo "  db-migrate-revision     Create new migration"
	@echo "  app-shell               Flask shell"
	@echo "  app-test                Run tests"
	@echo "  help                    Show this help message"
