#!/bin/bash -e
# Containerized smoke test runner, used by the harvester/release smoke
# workflows. Extra arguments are passed through to pytest.
#
# Outcome contract: results/ carries the HTML report and the marker file
# results/fail exists if the test run failed. The exit code stays 0 for
# infrastructure-level success so callers can distinguish "tests failed"
# from "could not run tests".

cd "$(dirname "$0")"

IMAGE="${SMOKE_IMAGE:-harvester-smoke-tests}"
MARKER="${SMOKE_MARKER:-smoke}"

docker build -t "$IMAGE" -f Dockerfile.smoke .

mkdir -p results
rm -f results/fail

if ! docker run --rm --network host \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp \
    -v "$PWD:/app" \
    "$IMAGE" \
    pytest harvester_e2e_tests -v -m "$MARKER" --html=results/api.html "$@"; then
  touch results/fail
  echo "Smoke tests failed, see results/"
fi
