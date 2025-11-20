# Embedding Service Unit Tests

## Overview
Comprehensive unit tests for the embedding service (`main.py`), covering all endpoints and core functions.

## Test Coverage

### Core Functions
- **`_encode()`**: Tests encoding single texts, normalization, error handling, consistency
- **`encode_text_cached()`**: Tests caching behavior, byte conversion, cache efficiency
- **`encode_list()`**: Tests batch encoding, shape validation, normalization

### API Endpoints
- **`GET /health`**: Health check endpoint
- **`GET /`**: Root endpoint
- **`POST /embed`**: Single and batch text embedding
- **`POST /index`**: Data indexing to Weaviate

### Test Categories
- **Unit Tests**: Individual function testing
- **Integration Tests**: Cross-function consistency
- **Error Handling**: Edge cases and validation

## Installation

Install test dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Running Tests

### Run all tests
```bash
pytest test_main.py -v
```

### Run with coverage
```bash
pytest test_main.py --cov=services.embedding.main --cov-report=html --cov-report=term
```

### Run specific test class
```bash
pytest test_main.py::TestEncodeFunction -v
```

### Run specific test
```bash
pytest test_main.py::TestEncodeFunction::test_encode_returns_numpy_array -v
```

### Run tests by marker
```bash
# Run only unit tests
pytest test_main.py -m unit -v

# Run only integration tests
pytest test_main.py -m integration -v
```

## Test Structure

```
services/embedding/
├── main.py              # Main application code
├── test_main.py         # Unit tests
├── pytest.ini           # Pytest configuration
├── requirements.txt     # Production dependencies
└── requirements-dev.txt # Development dependencies
```

## Key Test Cases

### 1. Encoding Tests
- Vector normalization (L2 norm ≈ 1.0)
- Consistency (same input → same output)
- Multilingual support
- Empty input handling

### 2. Caching Tests
- LRU cache functionality
- Cache hits/misses tracking
- Byte serialization/deserialization

### 3. API Tests
- Request validation
- Response format
- Error handling
- Edge cases (empty lists, invalid paths)

### 4. Indexing Tests
- DataFrame loading
- Batch operations
- Deterministic UUID generation
- Schema creation

## Mocking

Tests use mocking for:
- **Weaviate client**: Avoids need for running Weaviate instance
- **Database operations**: Tests logic without external dependencies

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
```bash
pytest test_main.py --junitxml=junit.xml --cov=services.embedding.main --cov-report=xml
```

## Notes

- Tests do NOT require a running Weaviate instance (mocked)
- Tests DO require the LaBSE model to be downloaded (first run may be slow)
- Cache tests verify actual caching behavior
- Integration tests ensure consistency between different code paths
