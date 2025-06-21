# Makefile - Project Management with Docker
# Template for fullstack Django + Next.js projects

.PHONY: help install dev prod build up down restart logs shell test clean

# ===== CONFIGURATION =====
include .env
export

DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_DEV = docker-compose -f docker-compose.yml -f docker-compose.override.yml
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.yml -f docker-compose.prod.yml

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[0;33m
BLUE = \033[0;34m
PURPLE = \033[0;35m
CYAN = \033[0;36m
NC = \033[0m

# ===== HELP =====
help: ## 📖 Show this help menu
	@echo "$(CYAN)🐳 ${PROJECT_NAME} - Docker Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)📋 MAIN COMMANDS:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)🔧 USAGE EXAMPLES:$(NC)"
	@echo "  $(BLUE)make install$(NC)       - Complete initial setup"
	@echo "  $(BLUE)make dev$(NC)           - Start in development mode"
	@echo "  $(BLUE)make logs$(NC)          - View real-time logs"
	@echo "  $(BLUE)make shell$(NC)         - Enter backend container"
	@echo "  $(BLUE)make test$(NC)          - Run all tests"
	@echo ""

# ===== SETUP & INSTALLATION =====
install: ## 🚀 Complete initial project setup
	@echo "$(CYAN)🚀 Setting up ${PROJECT_NAME}...$(NC)"
	@make check-requirements
	@make create-env
	@make build
	@make up-dev
	@make migrate
	@make create-superuser-auto
	@make load-fixtures
	@echo "$(GREEN)✅ Setup complete!$(NC)"
	@echo "$(BLUE)🌐 Backend API: http://localhost:${BACKEND_PORT}$(NC)"
	@echo "$(BLUE)🎨 Frontend: http://localhost:${FRONTEND_PORT}$(NC)"
	@echo "$(BLUE)🔧 Django Admin: http://localhost:${BACKEND_PORT}/admin$(NC)"
	@echo "$(BLUE)🌸 Flower: http://localhost:${FLOWER_PORT}$(NC)"
	@echo "$(BLUE)🗃️ PgAdmin: http://localhost:${PGADMIN_PORT}$(NC)"

check-requirements: ## 🔍 Check system requirements
	@echo "$(CYAN)🔍 Checking system requirements...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)❌ Docker not found. Please install Docker first.$(NC)"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "$(RED)❌ Docker Compose not found. Please install Docker Compose first.$(NC)"; exit 1; }
	@echo "$(GREEN)✅ Requirements verified!$(NC)"

create-env: ## 📝 Create .env file with default settings
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)📝 Creating .env file...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✅ .env file created! Edit as needed.$(NC)"; \
	else \
		echo "$(BLUE)ℹ️  .env file already exists.$(NC)"; \
	fi

# ===== DOCKER BASICS =====
build: ## 🔨 Build Docker images
	@echo "$(CYAN)🔨 Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build --parallel

build-no-cache: ## 🔨 Build without cache (useful for debugging)
	@echo "$(CYAN)🔨 Building without cache...$(NC)"
	$(DOCKER_COMPOSE) build --no-cache --parallel

pull: ## ⬇️ Pull base images
	@echo "$(CYAN)⬇️ Pulling base images...$(NC)"
	$(DOCKER_COMPOSE) pull

up: ## 🚀 Start all services (production)
	@echo "$(CYAN)🚀 Starting services in production mode...$(NC)"
	$(DOCKER_COMPOSE_PROD) up -d
	@make status

up-dev: ## 🧪 Start services in development mode
	@echo "$(CYAN)🧪 Starting services in development mode...$(NC)"
	$(DOCKER_COMPOSE_DEV) up -d
	@make status

down: ## 🛑 Stop all services
	@echo "$(CYAN)🛑 Stopping services...$(NC)"
	$(DOCKER_COMPOSE) down

down-volumes: ## 🛑 Stop services and remove volumes
	@echo "$(CYAN)🛑 Stopping services and removing volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v

restart: ## 🔄 Restart all services
	@echo "$(CYAN)🔄 Restarting services...$(NC)"
	@make down
	@make up-dev

# ===== ENVIRONMENTS =====
dev: up-dev ## 🧪 Alias for up-dev

prod: ## 🚀 Start production environment
	@echo "$(CYAN)🚀 Starting production environment...$(NC)"
	@make up
	@make status

# ===== LOGS =====
logs: ## 📋 View logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## 📋 View backend logs only
	$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## 📋 View frontend logs only
	$(DOCKER_COMPOSE) logs -f frontend

logs-celery: ## 📋 View Celery worker logs
	$(DOCKER_COMPOSE) logs -f celery_worker

logs-celery-beat: ## 📋 View Celery beat logs
	$(DOCKER_COMPOSE) logs -f celery_beat

logs-db: ## 📋 View PostgreSQL logs
	$(DOCKER_COMPOSE) logs -f postgres

logs-redis: ## 📋 View Redis logs
	$(DOCKER_COMPOSE) logs -f redis

logs-nginx: ## 📋 View Nginx logs
	$(DOCKER_COMPOSE) logs -f nginx

# ===== CONTAINER ACCESS =====
shell: ## 🐚 Access backend container shell
	$(DOCKER_COMPOSE) exec backend /bin/bash

shell-frontend: ## 🐚 Access frontend container shell
	$(DOCKER_COMPOSE) exec frontend /bin/sh

shell-db: ## 🐚 Access PostgreSQL
	$(DOCKER_COMPOSE) exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

shell-redis: ## 🐚 Access Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

django-shell: ## 🐍 Django interactive shell
	$(DOCKER_COMPOSE) exec backend python manage.py shell

# ===== DATABASE =====
migrate: ## 🗃️ Run database migrations
	@echo "$(CYAN)🗃️ Running migrations...$(NC)"
	$(DOCKER_COMPOSE) exec backend python manage.py migrate

makemigrations: ## 🗃️ Create new migrations
	@echo "$(CYAN)🗃️ Creating migrations...$(NC)"
	$(DOCKER_COMPOSE) exec backend python manage.py makemigrations

reset-db: ## ⚠️ Complete database RESET (CAUTION!)
	@echo "$(RED)⚠️  WARNING: This will DELETE ALL data!$(NC)"
	@read -p "Are you sure? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		make down; \
		docker volume rm $$(docker volume ls -q | grep ${PROJECT_PREFIX}.*postgres) 2>/dev/null || true; \
		make up-dev; \
		sleep 10; \
		make migrate; \
		make create-superuser-auto; \
		echo "$(GREEN)✅ Database reset complete!$(NC)"; \
	else \
		echo "$(BLUE)ℹ️  Operation cancelled.$(NC)"; \
	fi

backup-db: ## 💾 Backup database
	@echo "$(CYAN)💾 Backing up database...$(NC)"
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup saved in backups/$(NC)"

restore-db: ## 📥 Restore database backup
	@echo "$(CYAN)📥 Restoring backup...$(NC)"
	@ls -la backups/*.sql 2>/dev/null || (echo "$(RED)❌ No backup found in backups/$(NC)" && exit 1)
	@echo "Available backups:"
	@ls -1 backups/*.sql
	@read -p "Enter backup filename: " backup_file; \
	$(DOCKER_COMPOSE) exec -T postgres psql -U ${POSTGRES_USER} ${POSTGRES_DB} < backups/$$backup_file

load-fixtures: ## 📦 Load sample data
	@echo "$(CYAN)📦 Loading fixtures...$(NC)"
	$(DOCKER_COMPOSE) exec backend python manage.py loaddata fixtures/initial_data.json 2>/dev/null || echo "$(YELLOW)⚠️ Fixtures not found$(NC)"

# ===== USERS =====
create-superuser: ## 👤 Create Django superuser (interactive)
	$(DOCKER_COMPOSE) exec backend python manage.py createsuperuser

create-superuser-auto: ## 👤 Create default superuser
	@echo "$(CYAN)👤 Creating default superuser...$(NC)"
	$(DOCKER_COMPOSE) exec backend python manage.py shell -c " \
		from django.contrib.auth.models import User; \
		User.objects.filter(is_superuser=True).exists() or \
		User.objects.create_superuser('${DJANGO_SUPERUSER_USERNAME}', '${DJANGO_SUPERUSER_EMAIL}', '${DJANGO_SUPERUSER_PASSWORD}') and \
		print('✅ Superuser created: ${DJANGO_SUPERUSER_USERNAME}') or \
		print('ℹ️ Superuser already exists')"

# ===== TESTS =====
test: ## 🧪 Run all tests
	@echo "$(CYAN)🧪 Running tests...$(NC)"
	$(DOCKER_COMPOSE) exec backend python -m pytest -v --cov=apps --cov-report=term-missing

test-unit: ## 🧪 Run unit tests only
	$(DOCKER_COMPOSE) exec backend python -m pytest tests/unit/ -v

test-integration: ## 🧪 Run integration tests
	$(DOCKER_COMPOSE) exec backend python -m pytest tests/integration/ -v

test-watch: ## 🧪 Run tests in watch mode
	$(DOCKER_COMPOSE) exec backend python -m pytest --looponfail

coverage: ## 📊 Generate HTML coverage report
	$(DOCKER_COMPOSE) exec backend python -m pytest --cov=apps --cov-report=html
	@echo "$(GREEN)✅ Report generated in htmlcov/index.html$(NC)"

# ===== CODE QUALITY =====
lint: ## 🔍 Check code quality
	@echo "$(CYAN)🔍 Checking code quality...$(NC)"
	$(DOCKER_COMPOSE) exec backend flake8 .
	$(DOCKER_COMPOSE) exec backend black --check .

format: ## 🎨 Format code automatically
	@echo "$(CYAN)🎨 Formatting code...$(NC)"
	$(DOCKER_COMPOSE) exec backend black .
	$(DOCKER_COMPOSE) exec backend isort .

# ===== MONITORING =====
status: ## 📊 View status of all services
	@echo "$(CYAN)📊 Service Status:$(NC)"
	@$(DOCKER_COMPOSE) ps --format "table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

health: ## 🏥 Check service health
	@echo "$(CYAN)🏥 Service Health Check:$(NC)"
	@echo ""
	@echo "$(YELLOW)🔗 Backend API:$(NC)"
	@curl -f -s http://localhost:${BACKEND_PORT}/health/ > /dev/null && echo "$(GREEN)✅ Backend OK$(NC)" || echo "$(RED)❌ Backend FAILED$(NC)"
	@echo ""
	@echo "$(YELLOW)🎨 Frontend:$(NC)"
	@curl -f -s http://localhost:${FRONTEND_PORT} > /dev/null && echo "$(GREEN)✅ Frontend OK$(NC)" || echo "$(RED)❌ Frontend FAILED$(NC)"
	@echo ""
	@echo "$(YELLOW)🗃️ PostgreSQL:$(NC)"
	@$(DOCKER_COMPOSE) exec postgres pg_isready -U ${POSTGRES_USER} > /dev/null 2>&1 && echo "$(GREEN)✅ PostgreSQL OK$(NC)" || echo "$(RED)❌ PostgreSQL FAILED$(NC)"
	@echo ""
	@echo "$(YELLOW)📦 Redis:$(NC)"
	@$(DOCKER_COMPOSE) exec redis redis-cli ping 2>/dev/null | grep -q PONG && echo "$(GREEN)✅ Redis OK$(NC)" || echo "$(RED)❌ Redis FAILED$(NC)"

monitor: ## 📈 Open monitoring tools
	@echo "$(CYAN)📈 Monitoring Tools:$(NC)"
	@echo "$(BLUE)🌸 Flower (Celery): http://localhost:${FLOWER_PORT}$(NC)"
	@echo "$(BLUE)🔧 Django Admin: http://localhost:${BACKEND_PORT}/admin/$(NC)"
	@echo "$(BLUE)📊 API Health: http://localhost:${BACKEND_PORT}/health/$(NC)"
	@echo "$(BLUE)🗃️ PgAdmin: http://localhost:${PGADMIN_PORT}$(NC)"

stats: ## 📊 System statistics
	@echo "$(CYAN)📊 System Statistics:$(NC)"
	@echo ""
	@echo "$(YELLOW)🐳 Containers:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Size}}" | grep ${PROJECT_PREFIX} || echo "No ${PROJECT_NAME} containers running"
	@echo ""
	@echo "$(YELLOW)💾 Volumes:$(NC)"
	@docker volume ls | grep ${PROJECT_PREFIX} || echo "No ${PROJECT_NAME} volumes found"
	@echo ""
	@echo "$(YELLOW)🖼️ Images:$(NC)"
	@docker images | grep ${PROJECT_PREFIX} || echo "No ${PROJECT_NAME} images found"

# ===== CELERY =====
celery-status: ## 🌸 Celery status
	$(DOCKER_COMPOSE) exec celery_worker celery -A config status

celery-restart: ## 🌸 Restart Celery workers
	$(DOCKER_COMPOSE) restart celery_worker celery_beat

celery-purge: ## 🌸 Purge Celery queue
	$(DOCKER_COMPOSE) exec celery_worker celery -A config purge -f

celery-inspect: ## 🌸 Inspect Celery workers
	$(DOCKER_COMPOSE) exec celery_worker celery -A config inspect active

# ===== DEVELOPMENT =====
collect-static: ## 📦 Collect static files
	$(DOCKER_COMPOSE) exec backend python manage.py collectstatic --noinput

install-requirements: ## 📦 Install new dependencies
	$(DOCKER_COMPOSE) exec backend pip install -r requirements/development.txt

freeze-requirements: ## 📦 Generate current requirements.txt
	$(DOCKER_COMPOSE) exec backend pip freeze > requirements-generated.txt

# ===== DEPLOYMENT =====
deploy-staging: ## 🚀 Deploy to staging
	@echo "$(CYAN)🚀 Deploying to staging...$(NC)"
	git push origin develop
	# Add specific staging deployment commands

deploy-prod: ## 🚀 Deploy to production
	@echo "$(CYAN)🚀 Deploying to production...$(NC)"
	@echo "$(RED)⚠️  Deploying to PRODUCTION!$(NC)"
	@read -p "Are you sure? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		git push origin main; \
		make prod; \
		echo "$(GREEN)✅ Deploy completed!$(NC)"; \
	else \
		echo "$(BLUE)ℹ️  Deploy cancelled.$(NC)"; \
	fi

# ===== CLEANUP =====
clean: ## 🧹 Complete cleanup (containers, volumes, images)
	@echo "$(CYAN)🧹 Complete cleanup...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

clean-logs: ## 🧹 Clean logs
	@echo "$(CYAN)🧹 Cleaning logs...$(NC)"
	$(DOCKER_COMPOSE) exec backend find /app/logs -type f -mtime +7 -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Old logs cleaned!$(NC)"

clean-cache: ## 🧹 Clear Redis cache
	@echo "$(CYAN)🧹 Clearing Redis cache...$(NC)"
	$(DOCKER_COMPOSE) exec redis redis-cli FLUSHDB
	@echo "$(GREEN)✅ Cache cleared!$(NC)"

clean-media: ## 🧹 Clean old media files
	@echo "$(CYAN)🧹 Cleaning old media files...$(NC)"
	$(DOCKER_COMPOSE) exec backend find /app/media -type f -mtime +30 -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Old media files cleaned!$(NC)"

# ===== SHORTCUTS =====
quick-start: install ## ⚡ Alias for install (quick setup)

restart-backend: ## 🔄 Restart backend only
	$(DOCKER_COMPOSE) restart backend

restart-frontend: ## 🔄 Restart frontend only
	$(DOCKER_COMPOSE) restart frontend

restart-db: ## 🔄 Restart database only
	$(DOCKER_COMPOSE) restart postgres

restart-celery: ## 🔄 Restart Celery only
	$(DOCKER_COMPOSE) restart celery_worker celery_beat

# ===== UTILITIES =====
ps: ## 📋 Show running containers
	$(DOCKER_COMPOSE) ps

top: ## 📊 Show container resource usage
	docker stats $(docker ps --format "{{.Names}}" | grep ${PROJECT_PREFIX})

exec: ## 🔧 Execute command in backend (e.g., make exec cmd="python manage.py shell")
	$(DOCKER_COMPOSE) exec backend $(cmd)

# ===== DEFAULT =====
.DEFAULT_GOAL := help