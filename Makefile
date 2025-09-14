up:
	docker compose up -d

down:
	docker compose down -v --remove-orphans

rebuild:
	docker compose build && docker compose up -d

web:
	docker compose build web && docker compose up -d --no-deps web

beat:
	docker compose build beat && docker compose up -d --no-deps web

worker:
	docker compose build worker && docker compose up -d --no-deps web

web-logs:
	docker compose logs -f web

beat-logs:
	docker compose logs -f beat

worker-logs:
	docker compose logs -f worker

clean-all:
	docker compose down -v --rmi local --remove-orphans
	docker system prune -af --volumes

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

reset:
	docker compose stop worker beat
	docker compose run --rm worker celery -A app purge -f
	docker compose exec redis redis-cli FLUSHALL
	docker compose up -d worker beat