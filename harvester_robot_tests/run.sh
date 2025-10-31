#!/bin/bash
set -e

# Harvester Robot Framework Test Runner
# Usage: ./run.sh [options]

# Default values
TEST_CASE=""
TEST_SUITE=""
INCLUDE_TAG=""
EXCLUDE_TAG=""
VARIABLES=""
LOG_LEVEL="INFO"
OUTPUT_DIR=${OUTPUT_DIR:-/tmp/harvester-test-report}

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

show_help() {
    cat << EOF
Harvester Robot Framework Test Runner

Usage: $0 [options]

Options:
    -t "test name"      Run specific test case
    -s "suite name"     Run specific test suite
    -i "tag"           Include tests with tag
    -e "tag"           Exclude tests with tag
    -v VAR:value       Set Robot Framework variable
    -L log_level       Set log level (TRACE|DEBUG|INFO|WARN|ERROR)
    -d output_dir      Set output directory
    -h                 Show this help

Examples:
    $0                                    # Run all tests
    $0 -t "Test VM Basic Lifecycle"       # Run specific test
    $0 -s "test_vm"                       # Run test suite
    $0 -i coretest                        # Run with tag
    $0 -i p0 -e backup                    # Include/exclude tags
    $0 -v WAIT_TIMEOUT:1200               # Set variable
    $0 -L DEBUG                           # Debug logging

Available Tags:
    Priority: p0, p1, p2
    Type: coretest, regression, negative, smoke, sanity
    Component: virtualmachines, images, volumes, networks, backup, ha
EOF
}

# Parse arguments
while getopts "t:s:i:e:v:L:d:h" opt; do
    case $opt in
        t) TEST_CASE="--test \"$OPTARG\"" ;;
        s) TEST_SUITE="--suite \"$OPTARG\"" ;;
        i) INCLUDE_TAG="--include $OPTARG" ;;
        e) EXCLUDE_TAG="--exclude $OPTARG" ;;
        v) VARIABLES="$VARIABLES --variable $OPTARG" ;;
        L) LOG_LEVEL=$OPTARG ;;
        d) OUTPUT_DIR=$OPTARG ;;
        h) show_help; exit 0 ;;
        \?) echo "Invalid option: -$OPTARG" >&2; show_help; exit 1 ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check Robot Framework
if ! command -v robot &> /dev/null; then
    echo -e "${RED}Error: Robot Framework not installed${NC}"
    echo "Install with: pip install -r requirements.txt"
    exit 1
fi

# Check virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# Load .env if exists
if [ -f .env ]; then
    echo -e "${GREEN}Loading .env file...${NC}"
    # Export variables from .env, skip comments and empty lines
    set -a
    source .env
    set +a
    echo -e "${GREEN}Environment variables loaded from .env${NC}"
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Copy .env.example to .env and configure: cp .env.example .env${NC}"
fi

# Check required variables
[[ -z "$HARVESTER_ENDPOINT" ]] && echo -e "${YELLOW}Warning: HARVESTER_ENDPOINT not set (using default)${NC}"

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/libs"

# Build command
ROBOT_CMD="robot"
ROBOT_CMD="$ROBOT_CMD --outputdir $OUTPUT_DIR"
ROBOT_CMD="$ROBOT_CMD --loglevel $LOG_LEVEL"
ROBOT_CMD="$ROBOT_CMD --timestampoutputs"
ROBOT_CMD="$ROBOT_CMD --consolecolors on"

[ -n "$TEST_CASE" ] && ROBOT_CMD="$ROBOT_CMD $TEST_CASE"
[ -n "$TEST_SUITE" ] && ROBOT_CMD="$ROBOT_CMD $TEST_SUITE"
[ -n "$INCLUDE_TAG" ] && ROBOT_CMD="$ROBOT_CMD $INCLUDE_TAG"
[ -n "$EXCLUDE_TAG" ] && ROBOT_CMD="$ROBOT_CMD $EXCLUDE_TAG"
[ -n "$VARIABLES" ] && ROBOT_CMD="$ROBOT_CMD $VARIABLES"

ROBOT_CMD="$ROBOT_CMD tests/"

# Print info
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Harvester Robot Framework Test Runner${NC}"
echo -e "${GREEN}======================================${NC}"
echo "Output: $OUTPUT_DIR"
echo "Log level: $LOG_LEVEL"
echo -e "${GREEN}======================================${NC}"
echo

# Run tests
echo -e "${GREEN}Running tests...${NC}"
eval $ROBOT_CMD
EXIT_CODE=$?

# Print results
echo
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Test Execution Completed${NC}"
echo -e "${GREEN}======================================${NC}"
echo "Exit code: $EXIT_CODE"
echo "Reports:"
echo "  - HTML Report: $OUTPUT_DIR/report.html"
echo "  - HTML Log: $OUTPUT_DIR/log.html"
echo "  - XML Output: $OUTPUT_DIR/output.xml"
echo

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

exit $EXIT_CODE
