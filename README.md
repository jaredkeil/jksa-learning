The backend API for JKSA Learning application.
Implemented with FastAPI.

### Usage:

A dockerfile should be present one level above the directory which contains `run.sh`
The server is started by the dockerfile: `CMD run.sh`

In `run.sh, we check for a "prestart" script. This performs migrations

#### Alembic commands

Create a new migration file:
```
$ docker compose exec web poetry run alembic revision --autogenerate -m "init"
```

Apply the migration:
```
$ docker compose exec web poetry run alembic upgrade head
```

Downgrade
```
$ docker compose exec web poetry run alembic downgrade -1
```

Check:
```
$ docker compose exec web poetry run alembic check
```

#### CI/CD
RUN chmod +x prestart.sh

Run pytests in docker
```
docker compose exec web poetry run pytest
```
