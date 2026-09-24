#!/bin/bash
# =============================================================================
# SAAM Validation Runner + Reconciliation Trigger
#
# Runs the comprehensive test suite for a service, parses results into a
# structured YAML artifact, then calls the reconciliation script to update
# the graph and generate Kiro remediation tasks.
#
# USAGE:
#   ./validation/run-and-reconcile.sh <service-name> [trigger]
#
# ARGUMENTS:
#   service-name    Name of the service (must match validation/<service>/ dir)
#   trigger         Optional: stage2_smoke | stage4_final | model_b_post_atx |
#                   model_a_inline | ci_pipeline (default: manual)
#
# PREREQUISITES:
#   - Service must be running (or use --start to auto-start)
#   - validation/<service>/comprehensive-test-suite.sh must exist
#   - python3 with pyyaml available (for reconciliation script)
#
# OUTPUT:
#   .saam/reconciliation/<service>/validation-run-<timestamp>.yaml
#   (then reconcile_validation.py updates graph + generates Kiro tasks)
# =============================================================================

set -uo pipefail

SERVICE="${1:-}"
TRIGGER="${2:-manual}"
START_SERVICE="${START_SERVICE:-false}"

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service-name> [trigger]"
    echo "Example: $0 order-service stage2_smoke"
    exit 1
fi

# Paths
WORKSPACE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUITE_DIR="$WORKSPACE_ROOT/validation/$SERVICE"
SUITE_SCRIPT="$SUITE_DIR/comprehensive-test-suite.sh"
SERVICE_DIR="$WORKSPACE_ROOT/sourcecode/$SERVICE"
OUTPUT_DIR="$WORKSPACE_ROOT/.saam/reconciliation/$SERVICE"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
RUN_ID="val-$(date +%Y%m%d-%H%M%S)"
ARTIFACT="$OUTPUT_DIR/validation-run-${RUN_ID}.yaml"

# Validation and sourcecode dirs may use different naming (e.g. validation/MS-01 vs
# sourcecode/MS-01-reference-data). Resolve each independently: try the exact name, then a
# prefix match (the leading service id, e.g. MS-01) under each root.
if [ ! -f "$SUITE_SCRIPT" ]; then
    ALT=$(find "$WORKSPACE_ROOT/validation" -maxdepth 1 -type d -name "${SERVICE%%[-_]*}*" | head -1)
    if [ -n "$ALT" ] && [ -f "$ALT/comprehensive-test-suite.sh" ]; then
        SUITE_DIR="$ALT"; SUITE_SCRIPT="$ALT/comprehensive-test-suite.sh"
    fi
fi
if [ ! -d "$SERVICE_DIR" ]; then
    ALT=$(find "$WORKSPACE_ROOT/sourcecode" -maxdepth 1 -type d -name "${SERVICE%%[-_]*}*" | head -1)
    [ -n "$ALT" ] && SERVICE_DIR="$ALT"
fi

if [ ! -f "$SUITE_SCRIPT" ]; then
    echo "ERROR: Test suite not found for '$SERVICE' (looked in validation/$SERVICE and prefix match)"
    exit 1
fi

if [ ! -d "$SERVICE_DIR" ]; then
    echo "ERROR: Service directory not found for '$SERVICE' (looked in sourcecode/$SERVICE and prefix match)"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "=== SAAM Validation: $SERVICE ==="
echo "  Trigger: $TRIGGER"
echo "  Suite: $SUITE_SCRIPT"
echo "  Artifact: $ARTIFACT"
echo ""

# --- Optional: start service ---
SERVICE_PID=""
if [ "$START_SERVICE" = "true" ]; then
    echo "[run-and-reconcile] Starting service..."
    cd "$SERVICE_DIR"

    # Detect stack and start accordingly
    if [ -f "package.json" ]; then
        # Node.js / NestJS / Express
        npm run build 2>/dev/null
        PORT="${PORT:-3000}"
        npm run start:test &
        SERVICE_PID=$!
        HEALTH_PATH="/health"
    elif [ -f "pom.xml" ]; then
        # Java / Spring Boot
        PORT="${PORT:-8080}"
        mvn -q spring-boot:run -Dspring-boot.run.profiles=local &
        SERVICE_PID=$!
        HEALTH_PATH="/actuator/health"
    elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
        # Python / FastAPI
        PORT="${PORT:-8000}"
        uvicorn main:app --port "$PORT" &
        SERVICE_PID=$!
        HEALTH_PATH="/health"
    elif [ -f "go.mod" ]; then
        # Go
        PORT="${PORT:-8080}"
        go run . &
        SERVICE_PID=$!
        HEALTH_PATH="/health"
    else
        echo "WARNING: Cannot detect stack in $SERVICE_DIR — no package.json, pom.xml, pyproject.toml, or go.mod"
        echo "Set START_SERVICE=false and start the service manually before running."
        cd "$WORKSPACE_ROOT"
        exit 1
    fi

    cd "$WORKSPACE_ROOT"

    # Wait for readiness (stack-agnostic health check)
    for i in $(seq 1 60); do
        curl -sf "http://localhost:$PORT$HEALTH_PATH" > /dev/null 2>&1 && break
        sleep 1
    done
fi

cleanup() {
    if [ -n "$SERVICE_PID" ]; then
        kill $SERVICE_PID 2>/dev/null || true
        wait $SERVICE_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# --- Run test suite and capture output ---
echo "[run-and-reconcile] Running comprehensive test suite..."
BUILD_START=$(date +%s)

TEST_OUTPUT=$(bash "$SUITE_SCRIPT" 2>&1) || true
TEST_EXIT_CODE=$?

BUILD_END=$(date +%s)
DURATION=$((BUILD_END - BUILD_START))

# --- Parse test output ---
# The comprehensive test suite outputs a summary line like:
#   TOTAL: 47 | PASSED: 45 | FAILED: 2 | SKIPPED: 0
# And per-test results like:
#   [PASS] Test 1: Create order with valid data (BR-OR-CRD-001)
#   [FAIL] Test 23: Late fee Gold tier (BR-PA-CAL-007) - Expected: 15.00, Got: 12.50

# SAAM comprehensive-test-suite.sh summary format (v2.0):
#   Total Tests:  <N>
#   Passed:       <N>
#   Failed:       <N>
# (legacy TOTAL:/PASSED:/FAILED: also supported as a fallback)
TOTAL=$(echo "$TEST_OUTPUT" | sed -n 's/.*Total Tests:[[:space:]]*\([0-9]*\).*/\1/p' | tail -1)
[ -z "$TOTAL" ] && TOTAL=$(echo "$TEST_OUTPUT" | sed -n 's/.*TOTAL:[[:space:]]*\([0-9]*\).*/\1/p' | tail -1)
TOTAL="${TOTAL:-0}"
PASSED=$(echo "$TEST_OUTPUT" | sed -n 's/.*Passed:[[:space:]]*\([0-9]*\).*/\1/p' | tail -1)
[ -z "$PASSED" ] && PASSED=$(echo "$TEST_OUTPUT" | sed -n 's/.*PASSED:[[:space:]]*\([0-9]*\).*/\1/p' | tail -1)
PASSED="${PASSED:-0}"
FAILED=$(echo "$TEST_OUTPUT" | sed -n 's/.*Failed:[[:space:]]*\([0-9]*\).*/\1/p' | tail -1)
[ -z "$FAILED" ] && FAILED=$(echo "$TEST_OUTPUT" | sed -n 's/.*FAILED:[[:space:]]*\([0-9]*\).*/\1/p' | tail -1)
FAILED="${FAILED:-0}"
SKIPPED="0"   # SAAM suites have ZERO skips by design

# Fallback: count ✅/❌ markers if summary not found
if [ "$TOTAL" = "0" ]; then
    PASSED=$(echo "$TEST_OUTPUT" | grep -c '✅ PASSED' || echo "0")
    FAILED=$(echo "$TEST_OUTPUT" | grep -c '❌ FAILED' || echo "0")
    TOTAL=$((PASSED + FAILED))
fi

# Calculate pass rate
if [ "$TOTAL" -gt 0 ]; then
    PASS_RATE=$(echo "scale=3; $PASSED / $TOTAL" | bc -l 2>/dev/null || echo "0")
else
    PASS_RATE="0"
fi

# SAAM BR-ID pattern: 2-3 uppercase segments + numeric suffix (BR-REF-RES-001, BR-CATPROD-001, BR-PAY-009b)
BRID_RE='BR-[A-Z]{2,8}(-[A-Z]{2,8})?-[0-9]{1,4}[a-z]?'

# The SAAM suite prints, per test, a block:
#   Test <N>: <name>
#     Rule: <BR-ID> | ...
#     ✅ PASSED   (or)   ❌ FAILED (<reason>)
# Walk the output pairing each test's BR-ID + name with its outcome marker.
PAIRED=$(echo "$TEST_OUTPUT" | awk -v re="$BRID_RE" '
  /Test [0-9]+:/ { tn=$0; sub(/.*Test /,"",tn); sub(/:.*/,"",tn); name=$0; sub(/.*Test [0-9]+:[[:space:]]*/,"",name); brid="" }
  /Rule:/ { if (match($0, re)) brid=substr($0, RSTART, RLENGTH) }
  /✅ PASSED/ { printf "PASS\t%s\t%s\t%s\n", tn, brid, name }
  /❌ FAILED/ { reason=$0; sub(/.*❌ FAILED[[:space:]]*/,"",reason); printf "FAIL\t%s\t%s\t%s :: %s\n", tn, brid, name, reason }
')

FAILURES=""
while IFS=$'\t' read -r st tn brid rest; do
    [ "$st" = "FAIL" ] || continue
    nm=$(echo "$rest" | sed 's/ :: .*//' | sed 's/"/\\"/g')
    rs=$(echo "$rest" | sed 's/.* :: //' | sed 's/"/\\"/g')
    FAILURES="${FAILURES}    - test_num: ${tn:-?}
      name: \"${nm}\"
      br_id: \"${brid:-UNKNOWN}\"
      reason: \"${rs:-assertion failed}\"
"
done <<< "$PAIRED"

PASSING_BR_IDS=$(echo "$PAIRED" | awk -F'\t' '$1=="PASS"{print $3}' | grep -E "$BRID_RE" | sort -u)
FAILING_BR_IDS=$(echo "$PAIRED" | awk -F'\t' '$1=="FAIL"{print $3}' | grep -E "$BRID_RE" | sort -u)
BR_IDS_PASSING_COUNT=$(printf '%s\n' "$PASSING_BR_IDS" | grep -cE 'BR-' || true)
BR_IDS_PASSING_COUNT=${BR_IDS_PASSING_COUNT:-0}
BR_IDS_FAILING_COUNT=$(printf '%s\n' "$FAILING_BR_IDS" | grep -cE 'BR-' || true)
BR_IDS_FAILING_COUNT=${BR_IDS_FAILING_COUNT:-0}

# Detect new BR-IDs in code (run detect_br_ids in scan-only mode)
NEW_CLAIMS=""
if command -v python3 &>/dev/null && [ -f "$WORKSPACE_ROOT/graph-mcp/scripts/detect_br_ids.py" ]; then
    # Quick scan for BR-IDs in source (without updating graph — just detection)
    CODE_BR_IDS=$(find "$SERVICE_DIR/src" -type f \( -name "*.java" -o -name "*.kt" -o -name "*.ts" -o -name "*.py" -o -name "*.cs" \) -exec grep -ohE 'BR-[A-Z]{2,8}(-[A-Z]{2,8})?-[0-9]{1,4}[a-z]?' {} \; 2>/dev/null | sort -u)
    NEW_CLAIMS_LIST=$(echo "$CODE_BR_IDS" | tr '\n' ',' | sed 's/,$//')
fi

# --- Write YAML artifact ---
cat > "$ARTIFACT" << EOF
schema_version: "1.0"
service: "$SERVICE"
run_id: "$RUN_ID"
timestamp: "$TIMESTAMP"
trigger: "$TRIGGER"
implementation_type: "${IMPLEMENTATION_TYPE:-unknown}"

build:
  status: "$([ $TEST_EXIT_CODE -le 1 ] && echo 'pass' || echo 'fail')"
  duration_seconds: $DURATION

test_execution:
  suite: "comprehensive-test-suite.sh"
  total: $TOTAL
  passed: $PASSED
  failed: $FAILED
  skipped: $SKIPPED
  pass_rate: $PASS_RATE
  duration_seconds: $DURATION
  exit_code: $TEST_EXIT_CODE

  failures:
${FAILURES:-    []}

  br_ids_passing: $BR_IDS_PASSING_COUNT
  br_ids_failing: $BR_IDS_FAILING_COUNT

br_id_detection:
  code_br_ids: "${NEW_CLAIMS_LIST:-}"
EOF

echo ""
echo "=== Results ==="
echo "  Total: $TOTAL | Passed: $PASSED | Failed: $FAILED | Skipped: $SKIPPED"
echo "  Pass rate: $PASS_RATE"
echo "  BR-IDs passing: $BR_IDS_PASSING_COUNT | failing: $BR_IDS_FAILING_COUNT"
echo "  Artifact: $ARTIFACT"

# --- Call reconciliation script ---
RECONCILE_SCRIPT="$WORKSPACE_ROOT/graph-mcp/scripts/reconcile_validation.py"
if [ -f "$RECONCILE_SCRIPT" ]; then
    echo ""
    echo "[run-and-reconcile] Running graph reconciliation..."
    python3 "$RECONCILE_SCRIPT" "$ARTIFACT" || echo "WARNING: Reconciliation failed (graph may be unavailable)"
else
    echo ""
    echo "[run-and-reconcile] Reconciliation script not found — artifact produced but graph not updated"
fi

# --- Exit with test result ---
if [ "$FAILED" = "0" ] && [ "$TOTAL" -gt "0" ]; then
    echo ""
    echo "ALL TESTS PASSED for $SERVICE"
    exit 0
else
    echo ""
    echo "$FAILED test(s) failed for $SERVICE — see artifact for details"
    exit 1
fi
