#!/bin/sh

#export SQLALCHEMY_DATABASE_URI=${DATABASE_URL}  # from docker-compose yml services.web.environment

# If there's a prestart.sh script in the /app directory or other path specified, run it before starting
# PRE_START_PATH=${PRE_START_PATH:-/app/prestart.sh}
# echo "Checking for script in $PRE_START_PATH"
# if [ -f $PRE_START_PATH ] ; then
#    echo "Running script $PRE_START_PATH"
#    . "$PRE_START_PATH"
# else
#    echo "There is no script $PRE_START_PATH"
# fi

export APP_MODULE=${APP_MODULE-app.main:app}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8001}  # should be routed in docker-compose.yml
export BACKEND_CORS_ORIGINS=${BACKEND_CORS_ORIGINS}
export LOG_LEVEL=

# run gunicorn


#exec gunicorn --bind 0.0.0.0:8001 app.main:app -k uvicorn.workers.UvicornWorker --reload
#exec uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
exec uvicorn --reload --host $HOST --port $PORT --log-level debug "$APP_MODULE" --reload-exclude "test_*.py"

#exec gunicorn --bind $HOST:$PORT "$APP_MODULE" -k uvicorn.workers.UvicornWorker
