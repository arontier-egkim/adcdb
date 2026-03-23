.PHONY: db backend frontend seed structures

# Start MariaDB
db:
	docker compose up -d

# Run backend
backend:
	cd backend && uv run uvicorn app.main:app --port 8001 --host 0.0.0.0 --reload

# Run frontend
frontend:
	cd frontend && npm run dev

# Run database migrations
migrate:
	cd backend && uv run alembic upgrade head

# Seed database
seed:
	cd backend && uv run python ../data/seed.py

# Generate 3D structures
structures:
	cd backend && uv run python ../data/generate_structures.py

# Setup everything from scratch
setup: db
	@echo "Waiting for MariaDB..."
	@sleep 5
	$(MAKE) migrate
	$(MAKE) seed
	$(MAKE) structures
	@echo "Done. Run 'make backend' and 'make frontend' in separate terminals."
