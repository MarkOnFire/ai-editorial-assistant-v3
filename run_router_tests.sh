#!/bin/bash
# Quick test runner for router tests

source venv/bin/activate

echo "Running jobs router tests..."
python -m pytest tests/api/test_jobs_router.py -v --tb=short

echo ""
echo "Running queue router tests..."
python -m pytest tests/api/test_queue_router.py -v --tb=short

echo ""
echo "Tests complete!"
