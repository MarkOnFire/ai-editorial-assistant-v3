#!/bin/bash
# Editorial Assistant v3.0 - Development Session Initializer
#
# Run this at the start of each development session:
#   ./init.sh
#
# This script:
# 1. Ensures you're in the right directory
# 2. Activates the virtual environment (if exists)
# 3. Shows current progress status
# 4. Displays next available feature to work on

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================="
echo "Editorial Assistant v3.0 - Init"
echo "=================================="

# Check for virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment found"
    source venv/bin/activate
    echo "✓ Activated venv ($(python --version))"
else
    echo "⚠ No virtual environment found"
    echo "  Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# Show git status
echo ""
echo "Git Status:"
git branch --show-current
git status --short

# Show progress
echo ""
echo "=================================="
echo "Current Progress:"
echo "=================================="
if [ -f "claude-progress.txt" ]; then
    cat claude-progress.txt
else
    echo "No progress file found. Creating..."
    echo "# v3.0 Development Progress" > claude-progress.txt
    echo "" >> claude-progress.txt
    echo "Last updated: $(date)" >> claude-progress.txt
    echo "Current sprint: 2.1 (Foundation)" >> claude-progress.txt
    echo "" >> claude-progress.txt
    echo "## Session Notes" >> claude-progress.txt
fi

# Show next feature
echo ""
echo "=================================="
echo "Next Feature:"
echo "=================================="
if [ -f "feature_list.json" ]; then
    python3 -c "
import json
with open('feature_list.json') as f:
    features = json.load(f)
pending = [f for f in features if f.get('status') == 'pending']
in_progress = [f for f in features if f.get('status') == 'in_progress']
if in_progress:
    f = in_progress[0]
    print(f'IN PROGRESS: {f[\"id\"]} - {f[\"name\"]}')
    print(f'  Sprint: {f.get(\"sprint\", \"N/A\")}')
    print(f'  Description: {f.get(\"description\", \"N/A\")}')
elif pending:
    f = pending[0]
    print(f'NEXT: {f[\"id\"]} - {f[\"name\"]}')
    print(f'  Sprint: {f.get(\"sprint\", \"N/A\")}')
    print(f'  Description: {f.get(\"description\", \"N/A\")}')
else:
    print('All features complete!')
" 2>/dev/null || echo "Run: python3 to check feature_list.json"
else
    echo "No feature_list.json found"
fi

echo ""
echo "=================================="
echo "Ready for development!"
echo "=================================="
