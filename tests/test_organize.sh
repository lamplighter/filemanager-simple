#!/bin/bash

##############################################################################
# Basic Test Suite for File Organization System
#
# Tests core functionality of organize.sh and validate_suggestion.sh
##############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

run_test() {
    local test_name="$1"
    ((TESTS_RUN++))
    echo ""
    echo "Test $TESTS_RUN: $test_name"
    echo "----------------------------------------"
}

# Setup
setup() {
    echo "Setting up test environment..."
    cd "$PROJECT_DIR"

    # Create test directories
    mkdir -p tests/temp/{source,dest}

    # Backup state files
    if [[ -f state/file_queue.json ]]; then
        cp state/file_queue.json state/file_queue.json.backup
    fi
    if [[ -f state/move_history.json ]]; then
        cp state/move_history.json state/move_history.json.backup
    fi

    echo -e "${GREEN}Setup complete${NC}"
    echo ""
}

# Cleanup
cleanup() {
    echo ""
    echo "Cleaning up..."

    # Remove test files
    rm -rf tests/temp

    # Restore state files
    if [[ -f state/file_queue.json.backup ]]; then
        mv state/file_queue.json.backup state/file_queue.json
    fi
    if [[ -f state/move_history.json.backup ]]; then
        mv state/move_history.json.backup state/move_history.json
    fi

    echo -e "${GREEN}Cleanup complete${NC}"
}

# Tests
test_config_exists() {
    run_test "Configuration file exists"

    if [[ -f config.yaml ]]; then
        pass "config.yaml found"
    else
        fail "config.yaml not found"
    fi
}

test_scripts_executable() {
    run_test "Scripts are executable"

    if [[ -x organize.sh ]]; then
        pass "organize.sh is executable"
    else
        fail "organize.sh is not executable"
    fi

    if [[ -x scripts/validate_suggestion.sh ]]; then
        pass "validate_suggestion.sh is executable"
    else
        fail "validate_suggestion.sh is not executable"
    fi
}

test_state_files_exist() {
    run_test "State files exist"

    if [[ -f state/file_queue.json ]]; then
        pass "file_queue.json exists"
    else
        fail "file_queue.json missing"
    fi

    if [[ -f state/move_history.json ]]; then
        pass "move_history.json exists"
    else
        fail "move_history.json missing"
    fi
}

test_json_validity() {
    run_test "JSON files are valid"

    if jq empty state/file_queue.json 2>/dev/null; then
        pass "file_queue.json is valid JSON"
    else
        fail "file_queue.json is invalid JSON"
    fi

    if jq empty state/move_history.json 2>/dev/null; then
        pass "move_history.json is valid JSON"
    else
        fail "move_history.json is invalid JSON"
    fi
}

test_organize_help() {
    run_test "organize.sh --help works"

    if ./organize.sh --help > /dev/null 2>&1; then
        pass "organize.sh --help succeeded"
    else
        fail "organize.sh --help failed"
    fi
}

test_organize_status() {
    run_test "organize.sh --status works"

    if ./organize.sh --status > /dev/null 2>&1; then
        pass "organize.sh --status succeeded"
    else
        fail "organize.sh --status failed"
    fi
}

test_validate_suggestion() {
    run_test "validate_suggestion.sh works"

    # Create a test file
    touch tests/temp/source/test.pdf

    # Test validation (should pass)
    if ./scripts/validate_suggestion.sh \
        "$PROJECT_DIR/tests/temp/source/test.pdf" \
        "$PROJECT_DIR/tests/temp/dest/test.pdf" > /dev/null 2>&1; then
        pass "validate_suggestion.sh succeeded for valid paths"
    else
        fail "validate_suggestion.sh failed for valid paths"
    fi

    # Test validation (should fail - nonexistent source)
    if ! ./scripts/validate_suggestion.sh \
        "$PROJECT_DIR/tests/temp/source/nonexistent.pdf" \
        "$PROJECT_DIR/tests/temp/dest/test.pdf" > /dev/null 2>&1; then
        pass "validate_suggestion.sh correctly failed for invalid source"
    else
        fail "validate_suggestion.sh should have failed for invalid source"
    fi
}

test_dry_run() {
    run_test "organize.sh --dry-run works"

    # Reset queue
    echo '{"schema_version": "1.0", "files": []}' > state/file_queue.json

    # Add a test entry
    cat > state/file_queue.json << 'EOF'
{
  "schema_version": "1.0",
  "files": [
    {
      "id": "test-uuid-1234",
      "source_path": "/tmp/test_source.txt",
      "dest_path": "/tmp/test_dest.txt",
      "confidence": 95,
      "confidence_factors": {"test": 95},
      "status": "pending",
      "timestamp": "2025-01-21T00:00:00Z",
      "reasoning": "Test entry"
    }
  ]
}
EOF

    # Run dry-run
    if ./organize.sh --dry-run > /dev/null 2>&1; then
        pass "organize.sh --dry-run succeeded"
    else
        fail "organize.sh --dry-run failed"
    fi

    # Reset queue
    echo '{"schema_version": "1.0", "files": []}' > state/file_queue.json
}

test_jq_dependency() {
    run_test "jq is installed"

    if command -v jq &> /dev/null; then
        pass "jq is installed"
    else
        fail "jq is not installed (required dependency)"
    fi
}

##############################################################################
# Main
##############################################################################

echo "========================================"
echo "File Organization System - Test Suite"
echo "========================================"
echo ""

# Check jq first
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed${NC}"
    echo "Install with: brew install jq"
    exit 1
fi

setup

# Run tests
test_config_exists
test_scripts_executable
test_state_files_exist
test_json_validity
test_jq_dependency
test_organize_help
test_organize_status
test_validate_suggestion
test_dry_run

cleanup

# Summary
echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Total tests run: $TESTS_RUN"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
