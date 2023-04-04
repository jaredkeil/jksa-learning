#!/usr/bin/env bash

set -e
echo "User: $(whoami)"
mkdir -p /app/cov
chown -R app:app /app/cov
export COVERAGE_FILE=/app/cov/.coverage
. $(poetry env info --path)/bin/activate
#pytest --cov=app app/tests
set -x
pytest --cov=app --cov-report=term-missing app/tests "${@}"
