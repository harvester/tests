#!/bin/bash
set -e

# Harvester Robot Framework Test Runner
# Usage: ./run.sh [options]

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# Default values
TEST_CASE=""
TEST_SUITE=""
TEST_FILE=""
PROCESSES=""
ORDERING_FILE=""
EXCLUDE_LVM=""
LVM_REQUESTED=""
STRATEGY=""
INCLUDE_TAG=""
INCLUDE_TAG_VALUE=""
EXCLUDE_TAG=""
VARIABLES=""
LOG_LEVEL=${ROBOT_LOG_LEVEL:-INFO}
OUTPUT_DIR=${ROBOT_OUTPUT_DIR:-/tmp/harvester-test-report}

show_help() {
    cat << EOF
Harvester Robot Framework Test Runner

Usage: $0 [options]

Options:
    -t "test name"      Run specific test case by name
    -s "suite name"     Run specific test suite by name
    -f "file path"      Run specific test file (e.g., tests/regression/vm/test_vm.robot)
    -i "tag"           Include tests with tag
    -e "tag"           Exclude tests with tag
    -v VAR:value       Set Robot Framework variable
    -L log_level       Set log level (TRACE|DEBUG|INFO|WARN|ERROR)
    -d output_dir      Set output directory
    -p N               Run suites in parallel with pabot (N processes)
    -o ordering_file   Control Pabot suite stages with an ordering file (requires -p)
    -S strategy        Operation strategy: crd (default) or rest (sets HARVESTER_OPERATION_STRATEGY)
    -W                 Skip virtual environment check
    -h                 Show this help

Examples:
    $0                                    # Run all tests
    $0 -t "Test VM Basic Lifecycle"       # Run specific test case
    $0 -s "test_vm"                       # Run a single test suite by name
    $0 -s vm                              # Run a whole category (vm/volume/image/addon/rancher)
    $0 -f tests/regression/vm/test_vm.robot  # Run specific test file
    $0 -i coretest                        # Run with tag
    $0 -i p0 -e backup                    # Include/exclude tags
    $0 -v WAIT_TIMEOUT:1200               # Set variable
    $0 -L DEBUG                           # Debug logging
    $0 -p 3 -i volume                     # Run volume suites in parallel (3 processes)
    $0 -p 3 -f tests/regression/addon/lvm   # Ordered LVM setup, parallel suites, and cleanup
    $0 -S rest -i volume                  # Run volume suites against the REST API
    $0 -i pr-baseline -p 8                # Run the PR baseline (image+VM+volume) in parallel

Available Tags:
    Priority: p0, p1, p2
    Type: coretest, regression, negative, smoke, sanity
    Component: virtualmachines, images, volumes, networks, backup, ha
    Suite set: pr-baseline (all image + basic VM + volume suites for per-PR checks)
EOF
}

# Parse arguments
while getopts "t:s:f:i:e:v:L:d:p:o:S:Wh" opt; do
    case $opt in
        t) TEST_CASE="--test \"$OPTARG\"" ;;
        s) TEST_SUITE="--suite \"$OPTARG\"" ;;
        f) TEST_FILE="$OPTARG" ;;
        i) INCLUDE_TAG="--include $OPTARG"; INCLUDE_TAG_VALUE="$OPTARG" ;;
        e) EXCLUDE_TAG="--exclude $OPTARG" ;;
        v) VARIABLES="$VARIABLES --variable $OPTARG" ;;
        L) LOG_LEVEL=$OPTARG ;;
        d) OUTPUT_DIR=$OPTARG ;;
        p) PROCESSES=$OPTARG ;;
        o) ORDERING_FILE=$OPTARG ;;
        S) STRATEGY=$OPTARG ;;
        W) SKIP_VENV_CHECK=true ;;
        h) show_help; exit 0 ;;
        \?) echo "Invalid option: -$OPTARG" >&2; show_help; exit 1 ;;
    esac
done

if [ -n "$ORDERING_FILE" ] && [ -z "$PROCESSES" ]; then
    echo -e "${RED}Error: -o requires parallel execution with -p${NC}"
    exit 1
fi

INCLUDE_TAG_LOWER=${INCLUDE_TAG_VALUE,,}
STRATEGY_LOWER=${STRATEGY,,}

if [[ "$TEST_FILE" == *"addon/lvm"* ]]; then
    LVM_REQUESTED=true
elif [[ "$ORDERING_FILE" == *"lvm-order.txt"* ]]; then
    LVM_REQUESTED=true
    TEST_FILE="tests/regression/addon/lvm"
elif [ "$INCLUDE_TAG_LOWER" = "lvm" ]; then
    LVM_REQUESTED=true
    TEST_FILE="tests/regression/addon/lvm"
elif [[ "$INCLUDE_TAG_LOWER" == *"lvm"* ]]; then
    echo -e "${RED}Error: LVM tag expressions are not supported${NC}"
    echo "Use: -f tests/regression/addon/lvm"
    exit 1
fi

if [ -n "$LVM_REQUESTED" ]; then
    if [ "$STRATEGY_LOWER" = "rest" ]; then
        echo -e "${RED}Error: LVM suites require the CRD operation strategy${NC}"
        exit 1
    fi
    if [ -n "$PROCESSES" ] && [ -z "$ORDERING_FILE" ]; then
        ORDERING_FILE="tests/regression/addon/lvm/lvm-order.txt"
    fi
else
    # LVM consumes a physical test disk and requires staged cleanup. Broad
    # serial and parallel runs exclude it unless the caller opts in explicitly.
    EXCLUDE_LVM=true
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check Robot Framework
if ! command -v robot &> /dev/null; then
    echo -e "${RED}Error: Robot Framework not installed${NC}"
    echo "Install with: pip install -r requirements.txt"
    exit 1
fi

# Check pabot when parallel execution is requested
if [ -n "$PROCESSES" ] && ! command -v pabot &> /dev/null; then
    echo -e "${RED}Error: pabot not installed (required for -p)${NC}"
    echo "Install with: pip install -r requirements.txt"
    exit 1
fi

# Check virtual environment (skip if -W is set)
if [[ "$SKIP_VENV_CHECK" != "true" ]] && [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# Check required variables
[[ -z "$HARVESTER_ENDPOINT" ]] && echo -e "${YELLOW}Warning: HARVESTER_ENDPOINT not set (using default)${NC}"

# Set Python path (../apiclient provides the shared harvester_api package)
export PYTHONPATH="${PYTHONPATH}:$(pwd)/libs:$(pwd)/../apiclient"

# Operation strategy (crd|rest). Read at library import time, so export before robot starts.
[ -n "$STRATEGY" ] && export HARVESTER_OPERATION_STRATEGY="$STRATEGY"

# Build command
# Use pabot for suite-level parallel execution when -p is given, otherwise plain robot.
# pabot-specific options (e.g. --processes) must precede the shared robot options.
if [ -n "$PROCESSES" ]; then
    ROBOT_CMD="pabot --processes $PROCESSES"
else
    ROBOT_CMD="robot"
fi
[ -n "$ORDERING_FILE" ] && ROBOT_CMD="$ROBOT_CMD --ordering $ORDERING_FILE"
ROBOT_CMD="$ROBOT_CMD --outputdir $OUTPUT_DIR"
ROBOT_CMD="$ROBOT_CMD --loglevel $LOG_LEVEL"
ROBOT_CMD="$ROBOT_CMD --timestampoutputs"
ROBOT_CMD="$ROBOT_CMD --consolecolors on"

[ -n "$TEST_CASE" ] && ROBOT_CMD="$ROBOT_CMD $TEST_CASE"
[ -n "$TEST_SUITE" ] && ROBOT_CMD="$ROBOT_CMD $TEST_SUITE"
[ -n "$INCLUDE_TAG" ] && ROBOT_CMD="$ROBOT_CMD $INCLUDE_TAG"
[ -n "$EXCLUDE_TAG" ] && ROBOT_CMD="$ROBOT_CMD $EXCLUDE_TAG"
[ -n "$EXCLUDE_LVM" ] && ROBOT_CMD="$ROBOT_CMD --exclude lvm"
[ -n "$VARIABLES" ] && ROBOT_CMD="$ROBOT_CMD $VARIABLES"

# Add test path - if TEST_FILE is specified, use it; otherwise use tests/ directory
if [ -n "$TEST_FILE" ]; then
    ROBOT_CMD="$ROBOT_CMD $TEST_FILE"
else
    ROBOT_CMD="$ROBOT_CMD tests/"
fi

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
