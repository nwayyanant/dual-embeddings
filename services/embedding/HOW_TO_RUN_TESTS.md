# How to Run Tests - Embedding Service

## Prerequisites

Make sure you're in the correct directory and have dependencies installed:

```powershell
cd c:\workshop\starter-test\dual-embeddings\services\embedding
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 🎯 Quick Start

### Run ALL tests
```powershell
pytest test_main.py -v
```

### Run all tests with coverage
```powershell
pytest test_main.py --cov=services.embedding.main --cov-report=term-missing
```

---

## 📋 Running Specific Test Classes

### Run all tests in `TestEncodeFunction` class
```powershell
pytest test_main.py::TestEncodeFunction -v
```

### Run all tests in `TestEncodeCached` class
```powershell
pytest test_main.py::TestEncodeCached -v
```

### Run all tests in `TestEncodeList` class
```powershell
pytest test_main.py::TestEncodeList -v
```

### Run all tests in `TestHealthEndpoint` class
```powershell
pytest test_main.py::TestHealthEndpoint -v
```

### Run all tests in `TestRootEndpoint` class
```powershell
pytest test_main.py::TestRootEndpoint -v
```

### Run all tests in `TestEmbedEndpoint` class
```powershell
pytest test_main.py::TestEmbedEndpoint -v
```

### Run all tests in `TestIndexEndpoint` class
```powershell
pytest test_main.py::TestIndexEndpoint -v
```

### Run all tests in `TestIntegration` class
```powershell
pytest test_main.py::TestIntegration -v
```

### Run all tests in `TestErrorHandling` class
```powershell
pytest test_main.py::TestErrorHandling -v
```

---

## 🔍 Running Individual Tests

### TestEncodeFunction Tests
```powershell
# Test that _encode returns a numpy array
pytest test_main.py::TestEncodeFunction::test_encode_returns_numpy_array -v

# Test that _encode returns normalized vectors
pytest test_main.py::TestEncodeFunction::test_encode_returns_normalized_vector -v

# Test that empty text raises ValueError
pytest test_main.py::TestEncodeFunction::test_encode_empty_text_raises_error -v

# Test consistent output for same text
pytest test_main.py::TestEncodeFunction::test_encode_consistent_output -v

# Test different texts produce different vectors
pytest test_main.py::TestEncodeFunction::test_encode_different_texts_different_vectors -v

# Test encoding multilingual text
pytest test_main.py::TestEncodeFunction::test_encode_multilingual_text -v
```

### TestEncodeCached Tests
```powershell
# Test cached encode returns bytes
pytest test_main.py::TestEncodeCached::test_cached_encode_returns_bytes -v

# Test bytes can be converted back to array
pytest test_main.py::TestEncodeCached::test_cached_encode_can_convert_back -v

# Test that cache is actually used
pytest test_main.py::TestEncodeCached::test_cached_encode_uses_cache -v

# Test cache clearing
pytest test_main.py::TestEncodeCached::test_cache_clear_works -v
```

### TestEncodeList Tests
```powershell
# Test encode_list returns numpy array
pytest test_main.py::TestEncodeList::test_encode_list_returns_numpy_array -v

# Test output has correct shape
pytest test_main.py::TestEncodeList::test_encode_list_correct_shape -v

# Test all vectors are normalized
pytest test_main.py::TestEncodeList::test_encode_list_normalized_vectors -v

# Test single item encoding
pytest test_main.py::TestEncodeList::test_encode_list_single_item -v

# Test empty list encoding
pytest test_main.py::TestEncodeList::test_encode_list_empty_list -v
```

### TestHealthEndpoint Tests
```powershell
# Test health check endpoint
pytest test_main.py::TestHealthEndpoint::test_health_endpoint -v
```

### TestRootEndpoint Tests
```powershell
# Test root endpoint
pytest test_main.py::TestRootEndpoint::test_root_endpoint -v
```

### TestEmbedEndpoint Tests
```powershell
# Test embedding a single text
pytest test_main.py::TestEmbedEndpoint::test_embed_single_text -v

# Test embedding multiple texts
pytest test_main.py::TestEmbedEndpoint::test_embed_multiple_texts -v

# Test embedding empty list
pytest test_main.py::TestEmbedEndpoint::test_embed_empty_list -v

# Test with normalize=False
pytest test_main.py::TestEmbedEndpoint::test_embed_with_normalize_false -v

# Test multilingual embedding
pytest test_main.py::TestEmbedEndpoint::test_embed_multilingual -v

# Test vector length consistency
pytest test_main.py::TestEmbedEndpoint::test_embed_vector_length_consistency -v
```

### TestIndexEndpoint Tests
```powershell
# Test successful indexing
pytest test_main.py::TestIndexEndpoint::test_index_success -v

# Test ensure_schema is called
pytest test_main.py::TestIndexEndpoint::test_index_calls_ensure_schema -v

# Test batch operations
pytest test_main.py::TestIndexEndpoint::test_index_batch_operations -v

# Test deterministic UUIDs
pytest test_main.py::TestIndexEndpoint::test_index_deterministic_uuids -v

# Test invalid parquet path
pytest test_main.py::TestIndexEndpoint::test_index_invalid_parquet_path -v
```

### TestIntegration Tests
```powershell
# Test encode and embed consistency
pytest test_main.py::TestIntegration::test_encode_and_embed_consistency -v

# Test batch vs single encoding
pytest test_main.py::TestIntegration::test_batch_vs_single_encoding -v
```

### TestErrorHandling Tests
```powershell
# Test missing texts field
pytest test_main.py::TestErrorHandling::test_embed_missing_texts_field -v

# Test invalid JSON
pytest test_main.py::TestErrorHandling::test_embed_invalid_json -v

# Test missing parquet_path
pytest test_main.py::TestErrorHandling::test_index_missing_parquet_path -v
```

---

## 🎨 Advanced Options

### Run with detailed output
```powershell
pytest test_main.py -vv
```

### Run with full traceback on failures
```powershell
pytest test_main.py -v --tb=long
```

### Run with short traceback
```powershell
pytest test_main.py -v --tb=short
```

### Stop on first failure
```powershell
pytest test_main.py -x
```

### Run last failed tests only
```powershell
pytest test_main.py --lf
```

### Run failed tests first, then others
```powershell
pytest test_main.py --ff
```

### Show print statements
```powershell
pytest test_main.py -v -s
```

### Run tests matching a keyword
```powershell
# Run all tests with "encode" in the name
pytest test_main.py -k "encode" -v

# Run all tests with "cache" in the name
pytest test_main.py -k "cache" -v

# Run all tests with "endpoint" in the name
pytest test_main.py -k "endpoint" -v

# Run all tests with "multilingual" in the name
pytest test_main.py -k "multilingual" -v

# Run all tests with "error" in the name
pytest test_main.py -k "error" -v
```

### Run tests in parallel (requires pytest-xdist)
```powershell
# First install: pip install pytest-xdist
pytest test_main.py -n auto
```

---

## 📊 Coverage Reports

### Terminal coverage report
```powershell
pytest test_main.py --cov=services.embedding.main --cov-report=term
```

### Terminal coverage with missing lines
```powershell
pytest test_main.py --cov=services.embedding.main --cov-report=term-missing
```

### HTML coverage report (opens in browser)
```powershell
pytest test_main.py --cov=services.embedding.main --cov-report=html
# Then open: htmlcov/index.html
```

### XML coverage report (for CI/CD)
```powershell
pytest test_main.py --cov=services.embedding.main --cov-report=xml
```

### Multiple coverage formats
```powershell
pytest test_main.py --cov=services.embedding.main --cov-report=term-missing --cov-report=html --cov-report=xml
```

---

## 🏷️ Using Test Markers

### Run only unit tests
```powershell
pytest test_main.py -m unit -v
```

### Run only integration tests
```powershell
pytest test_main.py -m integration -v
```

### Run only slow tests
```powershell
pytest test_main.py -m slow -v
```

### Skip slow tests
```powershell
pytest test_main.py -m "not slow" -v
```

---

## 📝 Output Formats

### JUnit XML (for CI/CD)
```powershell
pytest test_main.py --junitxml=test-results.xml
```

### Generate test report
```powershell
pytest test_main.py -v > test-output.txt
```

### Quiet mode (minimal output)
```powershell
pytest test_main.py -q
```

### Summary only
```powershell
pytest test_main.py --tb=no
```

---

## 🔧 Debugging Tests

### Run in debug mode with pdb
```powershell
pytest test_main.py --pdb
```

### Drop into debugger on failure
```powershell
pytest test_main.py --pdb --maxfail=1
```

### Show local variables on failure
```powershell
pytest test_main.py -l
```

### Verbose with locals
```powershell
pytest test_main.py -vv -l
```

---

## 📦 Using the Run Scripts

### PowerShell script (Windows)
```powershell
.\run_tests.ps1
```

### Bash script (Linux/Mac/Git Bash)
```bash
./run_tests.sh
```

---

## 🎯 Common Workflows

### Quick check before commit
```powershell
pytest test_main.py -x --tb=short
```

### Full test suite with coverage
```powershell
pytest test_main.py -v --cov=services.embedding.main --cov-report=term-missing --cov-report=html
```

### CI/CD pipeline
```powershell
pytest test_main.py -v --junitxml=junit.xml --cov=services.embedding.main --cov-report=xml --cov-report=term
```

### Development (watch mode - requires pytest-watch)
```powershell
# First install: pip install pytest-watch
ptw test_main.py -- -v
```

---

## 💡 Tips

1. **First run is slow**: The LaBSE model downloads on first use (~500MB)
2. **Use `-k` for quick testing**: Filter tests by name patterns
3. **Use `-x` for faster debugging**: Stop on first failure
4. **Check coverage**: Aim for >80% coverage
5. **Use `--lf`**: Re-run only failed tests after fixing

---

## 🐛 Troubleshooting

### Import errors
```powershell
# Make sure you're in the correct directory
cd c:\workshop\starter-test\dual-embeddings\services\embedding

# Set PYTHONPATH if needed
$env:PYTHONPATH = "c:\workshop\starter-test\dual-embeddings"
pytest test_main.py -v
```

### Model download issues
```powershell
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/LaBSE')"
```

### Clear pytest cache
```powershell
pytest --cache-clear
```

---

## 📚 Complete Test List

Total: **36 tests** across **9 test classes**

- TestEncodeFunction: 6 tests
- TestEncodeCached: 4 tests
- TestEncodeList: 5 tests
- TestHealthEndpoint: 1 test
- TestRootEndpoint: 1 test
- TestEmbedEndpoint: 8 tests
- TestIndexEndpoint: 6 tests
- TestIntegration: 2 tests
- TestErrorHandling: 3 tests
