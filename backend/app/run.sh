#!/bin/sh

#export SQLALCHEMY_DATABASE_URI=${DATABASE_URL}  # from docker-compose yml services.web.environment
#set -e
ls -la

echo "(API_ENV=$API_ENV)"
if [ "$API_ENV" = "dev" ]
 then
   echo "Activating poetry environment for dev"
   VENV="$(poetry env info --path)"
   echo "(VENV=$VENV)"
   . ${VENV}/bin/activate
   APP_PACKAGE_PATH="/app"
 else
   echo "Not dev"
   APP_PACKAGE_PATH=$(pip show "app" | grep Location | cut -d ' ' -f 2)
fi
export ALEMBIC_CONFIG="${APP_PACKAGE_PATH}/app/alembic.ini"

# If there's a prestart.sh script in the /app directory or other path specified, run it before starting
 PRE_START_PATH=${PRE_START_PATH:-/app/prestart.sh}
 echo "Checking for script in $PRE_START_PATH"
 if [ -f $PRE_START_PATH ] ; then
    echo "Running script $PRE_START_PATH"
    . "$PRE_START_PATH"
    echo "Finished running script $PRE_START_PATH"
 else
    echo "There is no script $PRE_START_PATH"
 fi

export APP_MODULE=${APP_MODULE-app.main:app}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}  # should be routed in docker-compose.yml
export BACKEND_CORS_ORIGINS=${BACKEND_CORS_ORIGINS}
export LOG_LEVEL="info"

# Run gunicorn/uvicorn
#exec uvicorn --reload --host $HOST --port $PORT --log-level debug "$APP_MODULE" --reload-exclude "test_*.py"
exec gunicorn --reload --bind $HOST:$PORT  "$APP_MODULE" -k uvicorn.workers.UvicornWorker -w 1 --log-level $LOG_LEVEL