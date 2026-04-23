#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
RESOLVE_SCRIPT="$REPO_ROOT/plugins/brainstorm/opencode/scripts/brainstorm-resolve-rules.sh"
TEST_FILENAME="brainstorm-rules.md"

passed=0
failed=0

WORK_DIR="$(mktemp -d)"
USER_DIR="$(mktemp -d)"
XDG_HOME="$(mktemp -d)"

assert_temp_dir() {
    local dir="$1"
    local tmpbase="${TMPDIR:-/tmp}"
    tmpbase="${tmpbase%/}"
    case "$dir" in
        "$tmpbase"/*) ;;
        *)
            echo "FATAL: $dir is not under $tmpbase, refusing to proceed" >&2
            exit 1
            ;;
    esac
}

assert_temp_dir "$WORK_DIR"
assert_temp_dir "$USER_DIR"
assert_temp_dir "$XDG_HOME"

cleanup() {
    rm -rf "$WORK_DIR" "$USER_DIR" "$XDG_HOME"
}
trap cleanup EXIT

run_resolve() {
    (cd "$WORK_DIR" && bash "$RESOLVE_SCRIPT" "$TEST_FILENAME" "$USER_DIR")
}

run_resolve_xdg() {
    (cd "$WORK_DIR" && XDG_CONFIG_HOME="$XDG_HOME" bash "$RESOLVE_SCRIPT" "$TEST_FILENAME")
}

assert_output() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"
    if [[ "$expected" == "$actual" ]]; then
        echo "  PASS: $test_name"
        passed=$((passed + 1))
    else
        echo "  FAIL: $test_name"
        echo "    expected: $(printf '%q' "$expected")"
        echo "    actual:   $(printf '%q' "$actual")"
        failed=$((failed + 1))
    fi
}

assert_empty() {
    local test_name="$1"
    local actual="$2"
    if [[ -z "$actual" ]]; then
        echo "  PASS: $test_name"
        passed=$((passed + 1))
    else
        echo "  FAIL: $test_name"
        echo "    expected empty output"
        echo "    actual: $(printf '%q' "$actual")"
        failed=$((failed + 1))
    fi
}

echo "testing brainstorm-resolve-rules.sh"
echo "==================================="

echo
echo "test 1: no files present"
rm -rf "$WORK_DIR/.opencode"
rm -f "${USER_DIR:?}/$TEST_FILENAME"
output="$(run_resolve)"
assert_empty "no files produces empty output" "$output"

echo
echo "test 2: only project file"
mkdir -p "$WORK_DIR/.opencode"
echo "project rules content" > "$WORK_DIR/.opencode/$TEST_FILENAME"
rm -f "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve)"
assert_output "project file content returned" "project rules content" "$output"

echo
echo "test 3: only explicit user dir"
rm -rf "$WORK_DIR/.opencode"
echo "user rules content" > "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve)"
assert_output "explicit user dir content returned" "user rules content" "$output"

echo
echo "test 4: both files present (project wins)"
mkdir -p "$WORK_DIR/.opencode"
echo "project rules content" > "$WORK_DIR/.opencode/$TEST_FILENAME"
echo "user rules content" > "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve)"
assert_output "project file takes precedence" "project rules content" "$output"

echo
echo "test 5: empty project file with user file present"
mkdir -p "$WORK_DIR/.opencode"
: > "$WORK_DIR/.opencode/$TEST_FILENAME"
echo "user rules content" > "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve)"
assert_output "user file returned when project file is empty" "user rules content" "$output"

echo
echo "test 6: no filename argument"
output="$(cd "$WORK_DIR" && bash "$RESOLVE_SCRIPT")"
assert_empty "no argument produces empty output" "$output"

echo
echo "test 7: XDG fallback"
rm -rf "$WORK_DIR/.opencode"
mkdir -p "$XDG_HOME/opencode"
echo "user via xdg" > "$XDG_HOME/opencode/$TEST_FILENAME"
rm -f "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve_xdg)"
assert_output "xdg fallback works" "user via xdg" "$output"

echo
echo "test 8: explicit argument overrides XDG fallback"
echo "from explicit argument" > "$USER_DIR/$TEST_FILENAME"
echo "from xdg" > "$XDG_HOME/opencode/$TEST_FILENAME"
output="$(run_resolve)"
assert_output "explicit argument overrides xdg" "from explicit argument" "$output"

echo
echo "==================================="
echo "results: $passed passed, $failed failed"

if [[ "$failed" -gt 0 ]]; then
    exit 1
fi
