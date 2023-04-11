#! /usr/bin/env bash

# Let the DB start
echo "Starting to check availability of DB to API container"
python -m app.backend_pre_start main
echo "Done checking availability"

# Run migrations
#python -m app.migration_commands db_revision_cmd --autogenerate -m "before launch"
#python /app/.venv/lib/python3.11/site-packages/app/migration_commands.py db_revision_cmd --autogenerate -m "before launch"
#python /app/.venv/lib/python3.11/site-packages/app/migration_commands.py db_upgrade_cmd head

#APP_PACKAGE_PATH=$(pip show "app" | grep Location | cut -d ' ' -f 2)
#echo "(APP_PACKAGE_PATH=$APP_PACKAGE_PATH)"
## prod: /app/.venv/lib/python3.11/site-packages/app/alembic.ini
#export ALEMBIC_CONFIG="${APP_PACKAGE_PATH}/app/alembic.ini"

echo "(ALEMBIC_CONFIG=$ALEMBIC_CONFIG)"
echo "Generating an Alembic revision, before launch"
alembic revision --autogenerate -m "before launch"
echo "Revision generated"

echo "Upgrading to \"head\" revision with Alembic"
alembic upgrade head
echo "Done upgrading with Alembic"

# Create initial data in DB
python -m app.initial_data main
