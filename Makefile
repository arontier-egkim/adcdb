.PHONY: db db-stop db-reset backend frontend install-backend install-frontend migrate seed add-lp-smiles structures setup wait-db

# ──────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────

# Start MariaDB container
db:
	docker compose up -d

# Stop MariaDB container
db-stop:
	docker compose down

# Destroy MariaDB volume and restart (WARNING: deletes all data)
db-reset:
	docker compose down -v
	docker compose up -d

# Wait for MariaDB to become healthy
wait-db:
	@echo "Waiting for MariaDB to be ready..."
	@timeout=60; while [ $$timeout -gt 0 ]; do \
		if docker exec adcdb-mariadb healthcheck.sh --connect --innodb_initialized 2>/dev/null; then \
			echo "MariaDB is ready."; \
			break; \
		fi; \
		sleep 2; \
		timeout=$$((timeout - 2)); \
	done; \
	if [ $$timeout -le 0 ]; then \
		echo "ERROR: MariaDB did not become ready in time."; \
		exit 1; \
	fi

# ──────────────────────────────────────────────
# Install dependencies
# ──────────────────────────────────────────────

install-backend:
	cd backend && uv sync

install-frontend:
	cd frontend && npm install

# ──────────────────────────────────────────────
# Run services
# ──────────────────────────────────────────────

# Start FastAPI dev server
backend:
	cd backend && uv run uvicorn app.main:app --port 8001 --host 0.0.0.0 --reload

# Start Vite dev server
frontend:
	cd frontend && npm run dev

# ──────────────────────────────────────────────
# Data pipeline
# ──────────────────────────────────────────────

# Run database migrations
migrate:
	cd backend && uv run alembic upgrade head

# Seed database with initial data
seed:
	cd backend && uv run python ../data/seed.py

# Add curated linker-payload SMILES to ADCs
add-lp-smiles:
	cd backend && uv run python ../data/add_lp_smiles.py

# Generate 3D PDB structures
structures:
	cd backend && uv run python ../data/generate_structures.py

# ──────────────────────────────────────────────
# Full setup
# ──────────────────────────────────────────────

# Setup everything from scratch
setup: db wait-db
	$(MAKE) migrate
	$(MAKE) seed
	$(MAKE) add-lp-smiles
	$(MAKE) structures
	@echo ""
	@echo "Setup complete. Run in separate terminals:"
	@echo "  make backend   # FastAPI on port 8001"
	@echo "  make frontend  # Vite on port 5173"
