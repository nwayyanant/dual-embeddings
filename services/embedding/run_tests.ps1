# Run unit tests for embedding service

Write-Host "Installing test dependencies..." -ForegroundColor Cyan
pip install -q -r requirements-dev.txt

Write-Host ""
Write-Host "Running unit tests..." -ForegroundColor Cyan
pytest test_main.py -v --tb=short

Write-Host ""
Write-Host "Running tests with coverage..." -ForegroundColor Cyan
pytest test_main.py --cov=services.embedding.main --cov-report=term-missing --cov-report=html

Write-Host ""
Write-Host "Coverage report generated in htmlcov/index.html" -ForegroundColor Green
