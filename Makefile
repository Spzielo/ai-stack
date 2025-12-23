.PHONY: dev prod down logs backup restore

# Colors
GREEN=\033[0;32m
NC=\033[0m # No Color

dev:
	@echo "${GREEN}Swapping to Development Environment...${NC}"
	@chmod +x scripts/dev.sh
	@./scripts/dev.sh

prod:
	@echo "${GREEN}Swapping to Production Environment...${NC}"
	@chmod +x scripts/prod.sh
	@./scripts/prod.sh

down:
	@docker compose down

logs:
	@docker compose logs -f

backup:
	@chmod +x scripts/backup_brain.sh
	@./scripts/backup_brain.sh

# Usage: make restore file=backups/xxx.sql
restore:
	@chmod +x scripts/restore_brain.sh
	@./scripts/restore_brain.sh $(file)
