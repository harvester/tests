#!/usr/bin/env bash
# Usage: ./docker-run.sh [options] [-- args]
#
# Builds and runs the Harvester Robot Framework E2E test suite in a container.
#
# Options:
#   --kubeconfig <path>  Kubeconfig file on the host (can be empty)
#                        If not provided, the script will look for KUBECONFIG in the .env file.
#   --env <file>         ENV file (default: .env in script directory)
#   --output <path>      Output path bind-mounted into container (default: /tmp/harvester-test-report)
#   --                   Pass remaining arguments to the run.sh script inside container
#
# Prepare .env and specify the KUBECONFIG path in it before running this script.
#
# Examples:
#   # make sure .env is edited correctly
#   ./docker-run.sh -s "Tests.Regression.Image.Test Image"
#   ./docker-run.sh --kubeconfig ~/.kube/config --output ./reports -- -s "Tests.Regression.Image.Test Image"
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Option parsing ---
ENV_FILE="$SCRIPT_DIR/.env"
KUBECONFIG_FILE=""
OUTPUT_PATH="/tmp/harvester-test-report"
DOCKER_RUN_ARGS=()
USER_ID="$(id -u):$(id -g)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig)
      KUBECONFIG_FILE="$2"
      shift 2
      ;;
    --env)
      ENV_FILE="$2"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --)
      shift
      DOCKER_RUN_ARGS=("$@")
      break
      ;;
    *)
      echo "Error: Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate ENV file exists
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: ENV file not found: $ENV_FILE"
  exit 1
fi

# Resolve kubeconfig: CLI arg takes priority, otherwise fall back to the one inside .env
if [[ -z "$KUBECONFIG_FILE" ]]; then
  KUBECONFIG_FILE=$( ( set -a; source "$ENV_FILE"; echo "${KUBECONFIG:-}" ) )
fi
if [[ -z "$KUBECONFIG_FILE" ]]; then
  echo "Error: KUBECONFIG not provided (via --kubeconfig or in $ENV_FILE)"
  exit 1
fi

# Ensure output directory exists locally (for the bind mount)
mkdir -p "$OUTPUT_PATH"

echo "Using KUBECONFIG file: $KUBECONFIG_FILE"
echo "Using ENV file: $ENV_FILE"
echo "Using output path: $OUTPUT_PATH"

# Create a temporary .env file to bind-mount into the container
ENV_TMPFILE=$(mktemp)
trap 'rm -f "$ENV_TMPFILE"' EXIT INT TERM
cp "$ENV_FILE" "$ENV_TMPFILE"
echo "KUBECONFIG=/kubeconfig" >> "$ENV_TMPFILE"

# build a docker image to run tests
export DOCKER_BUILDKIT=1
# Build the image
# Generate image tag from script directory path
IMG_HASH=$(echo -n "$SCRIPT_DIR" | sha256sum | cut -c1-8)
IMAGE_NAME="harvester-robot-tests:${IMG_HASH}"
echo "Building Docker image: ${IMAGE_NAME}"
docker build --progress=plain \
  --build-context dir_apiclient="${SCRIPT_DIR}/../apiclient" \
  -f ${SCRIPT_DIR}/Dockerfile \
  -t "${IMAGE_NAME}" "${SCRIPT_DIR}"

# Run the container
echo "Running tests with image $IMAGE_NAME"

DOCKER_EXTRA_ARGS="-it"
if [ -n "${CI:-}" ]; then
  DOCKER_EXTRA_ARGS="-e PYTHONUNBUFFERED=1"
fi

set -x
docker run $DOCKER_EXTRA_ARGS --rm \
  --user "${USER_ID}" \
  -e "KUBECONFIG=/kubeconfig" \
  -v "${ENV_TMPFILE}:/harvester-robot-tests/.env:ro" \
  -v "${KUBECONFIG_FILE}:/kubeconfig:ro" \
  -v "${OUTPUT_PATH}:/test-output:rw" \
  "${IMAGE_NAME}" -W -d /test-output "${DOCKER_RUN_ARGS[@]}"
