#!/bin/sh

#export SQLALCHEMY_DATABASE_URI=${DATABASE_URL}  # from docker-compose yml services.web.environment

. $(poetry env info --path)/bin/activate

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
export LOG_LEVEL=

# Run gunicorn
#exec uvicorn --reload --host $HOST --port $PORT --log-level debug "$APP_MODULE" --reload-exclude "test_*.py"
exec gunicorn --reload --bind $HOST:$PORT  "$APP_MODULE" -k uvicorn.workers.UvicornWorker -w 5 --log-level debug
