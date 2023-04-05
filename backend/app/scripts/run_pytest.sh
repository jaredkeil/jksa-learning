#!/usr/bin/env bash

echo "User: $(whoami)"
export COVERAGE_FILE=/app/cov/.coverage
#. $(poetry env info --path)/bin/activate
.

set -x
#pytest --cov=app --cov-report=term-missing app/tests "${@}"
pytest --pyargs app.tests "${@}"
