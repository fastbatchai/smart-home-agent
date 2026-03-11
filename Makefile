.PHONY: help build up down start stop restart clean rebuild

# Default target - show help
help:
	@echo "Smart Home Agent - Docker Compose Commands"
	@echo "==========================================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help      - Show this help message"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Build and start all services"
	@echo "  start     - Start existing services (without rebuild)"
	@echo "  down      - Stop and remove all containers"
	@echo "  stop      - Stop services without removing containers"
	@echo "  restart   - Restart all services"
	@echo "  rebuild   - Full rebuild (down, build, up)"
	@echo "  clean     - Remove all containers, volumes, and images"


# Build and start all services
up:
	@echo "Starting all services ..."
	docker compose up -d

# Start existing services (no rebuild)
start:
	@echo "Starting services..."
	docker compose start

# Stop and remove all containers
down:
	@echo "Stopping and removing containers..."
	docker compose down

# Stop services without removing containers
stop:
	@echo "Stopping services..."
	docker compose stop

# Restart all services
restart:
	@echo "Restarting services..."
	docker compose restart

# Remove everything (containers, volumes, images)
clean:
	@echo "Cleaning up all containers, volumes, and images..."
	docker compose down -v --rmi all
	@echo "Cleanup complete!"

# Build all Docker images
build:
	@echo "Building Docker images..."
	docker compose build

# Full rebuild workflow
rebuild:
	@echo "Full rebuild: stopping, removing, building, and starting..."
	docker compose down
	docker compose build --no-cache
	docker compose up -d
	@echo "Rebuild complete! Services are running."
