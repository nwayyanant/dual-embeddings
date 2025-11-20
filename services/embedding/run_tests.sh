#!/bin/bash
# Run unit tests for embedding service

echo "Installing test dependencies..."
pip install -q -r requirements-dev.txt

echo ""
echo "Running unit tests..."
pytest test_main.py -v --tb=short

echo ""
echo "Running tests with coverage..."
pytest test_main.py --cov=services.embedding.main --cov-report=term-missing --cov-report=html

echo ""
echo "Coverage report generated in htmlcov/index.html"
