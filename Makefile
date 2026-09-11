.PHONY: help up down logs build restart clean health pipeline seed infra ps

help:
	@echo "Criminal Network Analysis System"
	@echo ""
	@echo "  make up         Start the whole stack (builds on first run)"
	@echo "  make down       Stop everything"
	@echo "  make infra      Start only the databases (Neo4j, Postgres, Mongo, Redis)"
	@echo "  make health     Check every service's /health endpoint"
	@echo "  make pipeline   Run the end-to-end ingestion test with sample data"
	@echo "  make seed       Load the demo syndicate directly into Neo4j"
	@echo "  make logs       Tail logs from all services"
	@echo "  make ps         Show container status"
	@echo "  make restart    Rebuild and restart"
	@echo "  make clean      Stop and delete all data volumes"

up:
	docker compose up --build -d
	@echo "Dashboard: http://localhost:5173   API docs: http://localhost:8000/docs"

down:
	docker compose down

infra:
	docker compose up -d neo4j postgres mongodb redis

build:
	docker compose build

restart:
	docker compose down && docker compose up --build -d

ps:
	docker compose ps

logs:
	docker compose logs -f

health:
	python integration/health_check.py

pipeline:
	python integration/data_pipeline.py

seed:
	cd graph_service && python seed_data.py

clean:
	docker compose down -v
