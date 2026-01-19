#!/bin/bash
# ABOUTME: Integration test for path portability in Docker
# ABOUTME: Verifies that {{CLAUDE_HOME}} and {{USER_HOME}} placeholders expand correctly

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "Path Portability Integration Test"
echo "================================================"
echo ""
echo "Running as user: $(whoami)"
echo "Home directory: $HOME"
echo "Expected CLAUDE_HOME: $HOME/.claude"
echo ""

# Create test directory structure
TEST_DIR=$(mktemp -d)
echo "Test directory: $TEST_DIR"
echo ""

# Create a config file with placeholders (simulating a published config)
mkdir -p "$TEST_DIR/plugins"
cat > "$TEST_DIR/settings.json" << 'EOF'
{
  "pluginPath": "{{CLAUDE_HOME}}/plugins/cache",
  "projectsDir": "{{USER_HOME}}/projects",
  "nested": {
    "deep": {
      "path": "{{CLAUDE_HOME}}/deep/nested/path"
    }
  },
  "arrayPaths": [
    "{{CLAUDE_HOME}}/path1",
    "{{USER_HOME}}/path2"
  ],
  "nonPathValue": "just a string",
  "number": 42,
  "enabled": true
}
EOF

cat > "$TEST_DIR/plugins/marketplace.json" << 'EOF'
{
  "marketplaces": [
    {
      "name": "official",
      "url": "https://example.com",
      "cachePath": "{{CLAUDE_HOME}}/plugins/cache/official"
    }
  ]
}
EOF

echo "Created test config files with placeholders:"
echo ""
echo "--- settings.json ---"
cat "$TEST_DIR/settings.json"
echo ""
echo "--- plugins/marketplace.json ---"
cat "$TEST_DIR/plugins/marketplace.json"
echo ""

# Run the import expansion
echo "================================================"
echo "Running path expansion (simulating import)..."
echo "================================================"
echo ""

python3 << PYTHON
import json
from pathlib import Path
from cenv.path_portability import process_json_files_for_import

test_dir = Path("$TEST_DIR")
process_json_files_for_import(test_dir)
print("Expansion complete!")
PYTHON

echo ""
echo "--- Expanded settings.json ---"
cat "$TEST_DIR/settings.json"
echo ""
echo "--- Expanded plugins/marketplace.json ---"
cat "$TEST_DIR/plugins/marketplace.json"
echo ""

# Verify the expansion
echo "================================================"
echo "Verifying expanded paths..."
echo "================================================"
echo ""

ERRORS=0

verify_path() {
    local file="$1"
    local jq_path="$2"
    local expected="$3"
    local actual

    actual=$(python3 -c "import json; print(json.load(open('$file'))$jq_path)")

    if [ "$actual" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} $file $jq_path"
        echo "  Expected: $expected"
        echo "  Got:      $actual"
    else
        echo -e "${RED}✗${NC} $file $jq_path"
        echo "  Expected: $expected"
        echo "  Got:      $actual"
        ERRORS=$((ERRORS + 1))
    fi
    echo ""
}

# Check each path
verify_path "$TEST_DIR/settings.json" "['pluginPath']" "$HOME/.claude/plugins/cache"
verify_path "$TEST_DIR/settings.json" "['projectsDir']" "$HOME/projects"
verify_path "$TEST_DIR/settings.json" "['nested']['deep']['path']" "$HOME/.claude/deep/nested/path"
verify_path "$TEST_DIR/settings.json" "['arrayPaths'][0]" "$HOME/.claude/path1"
verify_path "$TEST_DIR/settings.json" "['arrayPaths'][1]" "$HOME/path2"
verify_path "$TEST_DIR/plugins/marketplace.json" "['marketplaces'][0]['cachePath']" "$HOME/.claude/plugins/cache/official"

# Check non-path values are preserved
echo "Checking non-path values preserved..."
NON_PATH=$(python3 -c "import json; print(json.load(open('$TEST_DIR/settings.json'))['nonPathValue'])")
if [ "$NON_PATH" = "just a string" ]; then
    echo -e "${GREEN}✓${NC} Non-path string preserved"
else
    echo -e "${RED}✗${NC} Non-path string modified: $NON_PATH"
    ERRORS=$((ERRORS + 1))
fi

NUMBER=$(python3 -c "import json; print(json.load(open('$TEST_DIR/settings.json'))['number'])")
if [ "$NUMBER" = "42" ]; then
    echo -e "${GREEN}✓${NC} Number preserved"
else
    echo -e "${RED}✗${NC} Number modified: $NUMBER"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check that no placeholders remain
echo "Checking no placeholders remain..."
if grep -r "{{CLAUDE_HOME}}\|{{USER_HOME}}" "$TEST_DIR" > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Found unexpanded placeholders!"
    grep -r "{{CLAUDE_HOME}}\|{{USER_HOME}}" "$TEST_DIR"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓${NC} No unexpanded placeholders found"
fi
echo ""

# Cleanup
rm -rf "$TEST_DIR"

# Summary
echo "================================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$ERRORS test(s) failed!${NC}"
    exit 1
fi
