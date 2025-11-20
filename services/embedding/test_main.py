# services/embedding/test_main.py
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
import uuid
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Import the app and functions to test
from services.embedding.main import (
    app,
    _encode,
    encode_text_cached,
    encode_list,
    CLASS,
)


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_texts():
    """Sample texts for testing"""
    return [
        "This is a test sentence.",
        "Another example text for testing.",
        "नमस्ते, यह एक परीक्षण है।",  # Hindi text
        "こんにちは世界",  # Japanese text
    ]


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for index testing"""
    data = {
        "doc_id": ["doc_1", "doc_2", "doc_3"],
        "book_id": ["book_1", "book_1", "book_2"],
        "para_id": ["p1", "p2", "p3"],
        "pali_paragraph": ["Pali text 1", "Pali text 2", "Pali text 3"],
        "pali_paragraph_ascii": ["Pali ascii 1", "Pali ascii 2", "Pali ascii 3"],
        "translation_paragraph": ["Translation 1", "Translation 2", "Translation 3"],
        "translation_paragraph_ascii": ["Trans ascii 1", "Trans ascii 2", "Trans ascii 3"],
        "multilingual_concat": [
            "Pali text 1 Translation 1",
            "Pali text 2 Translation 2",
            "Pali text 3 Translation 3",
        ],
    }
    return pd.DataFrame(data)


class TestEncodeFunction:
    """Tests for _encode function"""

    def test_encode_returns_numpy_array(self):
        """Test that _encode returns a numpy array"""
        text = "Hello"
        result = _encode(text)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32

    def test_encode_returns_normalized_vector(self):
        """Test that _encode returns normalized vectors"""
        text = "Test sentence"
        result = _encode(text)
        # Check that the L2 norm is approximately 1 (normalized)
        norm = np.linalg.norm(result)
        assert np.isclose(norm, 1.0, atol=1e-5)

    def test_encode_empty_text_raises_error(self):
        """Test that empty text raises ValueError"""
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            _encode("")

    def test_encode_consistent_output(self):
        """Test that same text produces same vector"""
        text = "Consistent test"
        result1 = _encode(text)
        result2 = _encode(text)
        np.testing.assert_array_almost_equal(result1, result2)

    def test_encode_different_texts_different_vectors(self):
        """Test that different texts produce different vectors"""
        text1 = "First sentence"
        text2 = "Second sentence"
        result1 = _encode(text1)
        result2 = _encode(text2)
        # Vectors should not be identical
        assert not np.allclose(result1, result2)

    def test_encode_multilingual_text(self, sample_texts):
        """Test encoding multilingual texts"""
        for text in sample_texts:
            result = _encode(text)
            assert isinstance(result, np.ndarray)
            assert result.dtype == np.float32
            assert len(result.shape) == 1  # 1D vector


class TestEncodeCached:
    """Tests for encode_text_cached function"""

    def test_cached_encode_returns_bytes(self):
        """Test that cached encode returns bytes"""
        text = "Cache test"
        result = encode_text_cached(text)
        assert isinstance(result, bytes)

    def test_cached_encode_can_convert_back(self):
        """Test that cached bytes can be converted back to float32 array"""
        text = "Cache conversion test"
        raw_bytes = encode_text_cached(text)
        vec = np.frombuffer(raw_bytes, dtype=np.float32)
        
        # Should match direct encoding
        direct = _encode(text)
        np.testing.assert_array_almost_equal(vec, direct)

    def test_cached_encode_uses_cache(self):
        """Test that cache is actually used"""
        text = "Cache efficiency test"
        
        # Clear cache and get cache info
        encode_text_cached.cache_clear()
        info_before = encode_text_cached.cache_info()
        
        # First call - should miss cache
        encode_text_cached(text)
        info_after_first = encode_text_cached.cache_info()
        assert info_after_first.misses == info_before.misses + 1
        
        # Second call - should hit cache
        encode_text_cached(text)
        info_after_second = encode_text_cached.cache_info()
        assert info_after_second.hits == info_after_first.hits + 1

    def test_cache_clear_works(self):
        """Test that cache can be cleared"""
        encode_text_cached.cache_clear()
        info = encode_text_cached.cache_info()
        assert info.currsize == 0


class TestEncodeList:
    """Tests for encode_list function"""

    def test_encode_list_returns_numpy_array(self, sample_texts):
        """Test that encode_list returns numpy array"""
        result = encode_list(sample_texts)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32

    def test_encode_list_correct_shape(self, sample_texts):
        """Test that output has correct shape"""
        result = encode_list(sample_texts)
        assert result.shape[0] == len(sample_texts)
        assert len(result.shape) == 2  # 2D array

    def test_encode_list_normalized_vectors(self, sample_texts):
        """Test that all vectors are normalized"""
        result = encode_list(sample_texts)
        for vec in result:
            norm = np.linalg.norm(vec)
            assert np.isclose(norm, 1.0, atol=1e-5)

    def test_encode_list_single_item(self):
        """Test encoding a single-item list"""
        result = encode_list(["Single item"])
        assert result.shape[0] == 1

    def test_encode_list_empty_list(self):
        """Test encoding an empty list"""
        result = encode_list([])
        assert result.shape[0] == 0


class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestRootEndpoint:
    """Tests for / endpoint"""

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "embedding"
        assert data["status"] == "ok"


class TestEmbedEndpoint:
    """Tests for /embed endpoint"""

    def test_embed_single_text(self, client):
        """Test embedding a single text"""
        response = client.post("/embed", json={"texts": ["Test sentence"]})
        assert response.status_code == 200
        data = response.json()
        assert "vectors" in data
        assert len(data["vectors"]) == 1
        assert isinstance(data["vectors"][0], list)

    def test_embed_multiple_texts(self, client, sample_texts):
        """Test embedding multiple texts"""
        response = client.post("/embed", json={"texts": sample_texts})
        assert response.status_code == 200
        data = response.json()
        assert len(data["vectors"]) == len(sample_texts)

    def test_embed_empty_list(self, client):
        """Test embedding empty list"""
        response = client.post("/embed", json={"texts": []})
        assert response.status_code == 200
        data = response.json()
        assert data["vectors"] == []

    def test_embed_with_normalize_false(self, client):
        """Test embed endpoint with normalize=False"""
        response = client.post(
            "/embed", 
            json={"texts": ["Test"], "normalize": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["vectors"]) == 1

    def test_embed_multilingual(self, client):
        """Test embedding multilingual texts"""
        multilingual_texts = [
            "Hello world",
            "Bonjour le monde",
            "हेलो वर्ल्ड",
            "こんにちは世界",
        ]
        response = client.post("/embed", json={"texts": multilingual_texts})
        assert response.status_code == 200
        data = response.json()
        assert len(data["vectors"]) == len(multilingual_texts)

    def test_embed_vector_length_consistency(self, client):
        """Test that all vectors have the same length"""
        texts = ["Short", "A much longer sentence with many words"]
        response = client.post("/embed", json={"texts": texts})
        data = response.json()
        vectors = data["vectors"]
        assert len(vectors[0]) == len(vectors[1])


class TestIndexEndpoint:
    """Tests for /index endpoint"""

    @pytest.fixture
    def temp_parquet_file(self, sample_dataframe):
        """Create a temporary parquet file"""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            sample_dataframe.to_parquet(tmp.name)
            yield tmp.name
        # Cleanup
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

    @patch("services.embedding.main.weaviate.Client")
    @patch("services.embedding.main.ensure_schema")
    def test_index_success(
        self, mock_ensure_schema, mock_weaviate_client, client, temp_parquet_file
    ):
        """Test successful indexing"""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_weaviate_client.return_value = mock_client_instance
        mock_batch = MagicMock()
        mock_client_instance.batch.__enter__ = Mock(return_value=mock_batch)
        mock_client_instance.batch.__exit__ = Mock(return_value=False)
        mock_batch.batch_size = 256

        response = client.post(
            "/index",
            json={
                "parquet_path": temp_parquet_file,
                "batch_size": 5000,
                "include_langs": ["multilingual"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Index upsert complete"
        assert data["count"] == 3
        assert data["vector"] == "multilingual"

    @patch("services.embedding.main.weaviate.Client")
    @patch("services.embedding.main.ensure_schema")
    def test_index_calls_ensure_schema(
        self, mock_ensure_schema, mock_weaviate_client, client, temp_parquet_file
    ):
        """Test that indexing calls ensure_schema"""
        mock_client_instance = MagicMock()
        mock_weaviate_client.return_value = mock_client_instance
        mock_batch = MagicMock()
        mock_client_instance.batch.__enter__ = Mock(return_value=mock_batch)
        mock_client_instance.batch.__exit__ = Mock(return_value=False)

        client.post(
            "/index",
            json={"parquet_path": temp_parquet_file},
        )

        mock_ensure_schema.assert_called_once_with(mock_client_instance, named_vectors=False)

    @patch("services.embedding.main.weaviate.Client")
    @patch("services.embedding.main.ensure_schema")
    def test_index_batch_operations(
        self, mock_ensure_schema, mock_weaviate_client, client, temp_parquet_file
    ):
        """Test that batch operations are called correctly"""
        mock_client_instance = MagicMock()
        mock_weaviate_client.return_value = mock_client_instance
        mock_batch = MagicMock()
        mock_client_instance.batch.__enter__ = Mock(return_value=mock_batch)
        mock_client_instance.batch.__exit__ = Mock(return_value=False)

        client.post(
            "/index",
            json={"parquet_path": temp_parquet_file},
        )

        # Verify batch_size was set
        assert mock_batch.batch_size == 256
        # Verify add_data_object was called 3 times (for 3 rows)
        assert mock_batch.add_data_object.call_count == 3

    @patch("services.embedding.main.weaviate.Client")
    @patch("services.embedding.main.ensure_schema")
    def test_index_deterministic_uuids(
        self, mock_ensure_schema, mock_weaviate_client, client, temp_parquet_file
    ):
        """Test that UUIDs are deterministic based on doc_id"""
        mock_client_instance = MagicMock()
        mock_weaviate_client.return_value = mock_client_instance
        mock_batch = MagicMock()
        mock_client_instance.batch.__enter__ = Mock(return_value=mock_batch)
        mock_client_instance.batch.__exit__ = Mock(return_value=False)

        client.post(
            "/index",
            json={"parquet_path": temp_parquet_file},
        )

        # Get the UUIDs that were used
        calls = mock_batch.add_data_object.call_args_list
        uuids_used = [call.kwargs["uuid"] for call in calls]
        
        # Check that UUIDs are deterministic
        expected_uuid_1 = str(uuid.uuid5(uuid.NAMESPACE_DNS, "doc_1"))
        assert uuids_used[0] == expected_uuid_1

    def test_index_invalid_parquet_path(self, client):
        """Test indexing with invalid parquet path"""
        response = client.post(
            "/index",
            json={"parquet_path": "/nonexistent/file.parquet"},
        )
        # Should return an error (implementation may vary)
        assert response.status_code in [400, 500] or "error" in response.json()


class TestIntegration:
    """Integration tests"""

    def test_encode_and_embed_consistency(self, client):
        """Test that _encode and /embed endpoint produce consistent results"""
        text = "Integration test sentence"
        
        # Get vector from endpoint
        response = client.post("/embed", json={"texts": [text]})
        endpoint_vec = np.array(response.json()["vectors"][0], dtype=np.float32)
        
        # Get vector from direct function
        direct_vec = _encode(text)
        
        # Should be very close (allowing for serialization differences)
        np.testing.assert_array_almost_equal(endpoint_vec, direct_vec, decimal=5)

    def test_batch_vs_single_encoding(self, client):
        """Test that batch and single encoding produce same results"""
        texts = ["Test 1", "Test 2", "Test 3"]
        
        # Batch encode
        batch_response = client.post("/embed", json={"texts": texts})
        batch_vecs = batch_response.json()["vectors"]
        
        # Single encode each
        single_vecs = []
        for text in texts:
            response = client.post("/embed", json={"texts": [text]})
            single_vecs.append(response.json()["vectors"][0])
        
        # Should produce same results
        for batch_vec, single_vec in zip(batch_vecs, single_vecs):
            np.testing.assert_array_almost_equal(
                np.array(batch_vec), np.array(single_vec), decimal=5
            )


class TestErrorHandling:
    """Tests for error handling"""

    def test_embed_missing_texts_field(self, client):
        """Test embed endpoint with missing texts field"""
        response = client.post("/embed", json={})
        assert response.status_code == 422  # Validation error

    def test_embed_invalid_json(self, client):
        """Test embed endpoint with invalid JSON"""
        response = client.post(
            "/embed",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_index_missing_parquet_path(self, client):
        """Test index endpoint with missing parquet_path"""
        response = client.post("/index", json={})
        assert response.status_code == 422

class TestSingleWordEmbeddings:
    """Tests for single-word keyword embeddings quality and accuracy"""

    def test_single_word_embedding_normalized(self, client):
        """Test that single words return normalized vectors (norm ≈ 1.0)"""
        words = ["three", "hello", "world", "test"]
        for word in words:
            response = client.post("/embed", json={"texts": [word]})
            assert response.status_code == 200
            vec = np.array(response.json()["vectors"][0], dtype=np.float32)
            norm = np.linalg.norm(vec)
            assert np.isclose(norm, 1.0, atol=1e-5), f"Word '{word}' has norm {norm}, expected 1.0"

    def test_single_word_cache_performance(self, client):
        """Test that single words benefit from caching"""
        word = "three"
        # Clear cache first
        encode_text_cached.cache_clear()
        
        # First call
        response1 = client.post("/embed", json={"texts": [word]})
        info_after_first = encode_text_cached.cache_info()
        
        # Second call - should hit cache
        response2 = client.post("/embed", json={"texts": [word]})
        info_after_second = encode_text_cached.cache_info()
        
        assert response1.json()["vectors"] == response2.json()["vectors"]
        assert info_after_second.hits > info_after_first.hits

    def test_single_word_semantic_similarity(self, client):
        """Test semantic similarity between related single words"""
        # Related words should have higher cosine similarity
        word1 = "hello"
        word2 = "hi"
        word3 = "goodbye"
        
        response = client.post("/embed", json={"texts": [word1, word2, word3]})
        vecs = [np.array(v, dtype=np.float32) for v in response.json()["vectors"]]
        
        # Cosine similarity (dot product of normalized vectors)
        similarity_hello_hi = np.dot(vecs[0], vecs[1])
        similarity_hello_goodbye = np.dot(vecs[0], vecs[2])
        
        # "hello" should be more similar to "hi" than to "goodbye"
        assert similarity_hello_hi > similarity_hello_goodbye

    def test_single_word_number_embeddings(self, client):
        """Test that number words like 'three' produce valid embeddings"""
        numbers = ["one", "two", "three", "four", "five"]
        response = client.post("/embed", json={"texts": numbers})
        assert response.status_code == 200
        vectors = response.json()["vectors"]
        
        assert len(vectors) == len(numbers)
        for i, vec in enumerate(vectors):
            vec_array = np.array(vec, dtype=np.float32)
            assert vec_array.shape[0] > 0, f"Number '{numbers[i]}' has empty vector"
            assert not np.all(vec_array == 0), f"Number '{numbers[i]}' has zero vector"

    def test_single_word_distinctiveness(self, client):
        """Test that different single words produce distinct vectors"""
        words = ["three", "hello", "world", "test", "python"]
        response = client.post("/embed", json={"texts": words})
        vectors = [np.array(v, dtype=np.float32) for v in response.json()["vectors"]]
        
        # Check all pairs are sufficiently different
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                similarity = np.dot(vectors[i], vectors[j])
                # Unrelated words should have similarity < 1.0 (not identical)
                assert similarity < 0.99, f"'{words[i]}' and '{words[j]}' are too similar: {similarity}"

    def test_single_word_consistency_across_calls(self, client):
        """Test that same single word always produces same vector"""
        word = "hello"
        responses = [
            client.post("/embed", json={"texts": [word]})
            for _ in range(3)
        ]
        
        vectors = [np.array(r.json()["vectors"][0]) for r in responses]
        
        # All should be identical
        for i in range(1, len(vectors)):
            np.testing.assert_array_almost_equal(vectors[0], vectors[i], decimal=6)

    def test_single_word_multilingual(self, client):
        """Test single words in different languages"""
        multilingual_words = {
            "hello": "en",
            "नमस्ते": "hi",  # Hindi
            "こんにちは": "ja",  # Japanese
            "bonjour": "fr",
            "hola": "es"
        }
        
        response = client.post("/embed", json={"texts": list(multilingual_words.keys())})
        assert response.status_code == 200
        vectors = response.json()["vectors"]
        
        assert len(vectors) == len(multilingual_words)
        for vec in vectors:
            vec_array = np.array(vec, dtype=np.float32)
            norm = np.linalg.norm(vec_array)
            assert np.isclose(norm, 1.0, atol=1e-5)

    def test_single_word_special_cases(self, client):
        """Test edge cases for single words"""
        # Single character
        response = client.post("/embed", json={"texts": ["a"]})
        assert response.status_code == 200
        
        # Number digit
        response = client.post("/embed", json={"texts": ["3"]})
        assert response.status_code == 200
        
        # Punctuation (might be handled differently)
        response = client.post("/embed", json={"texts": ["!"]})
        assert response.status_code == 200

    def test_single_word_vector_dimensionality(self, client):
        """Test that single words produce vectors of expected dimension"""
        word = "three"
        response = client.post("/embed", json={"texts": [word]})
        vec = response.json()["vectors"][0]
        
        # LaBSE model produces 768-dimensional vectors
        assert len(vec) == 768, f"Expected 768 dimensions, got {len(vec)}"


class TestEmbeddingScoreQuality:
    """Tests for embedding quality using similarity scores"""

    def test_identical_text_perfect_score(self, client):
        """Test that identical texts have similarity score ≈ 1.0"""
        text = "three"
        response = client.post("/embed", json={"texts": [text, text]})
        vecs = [np.array(v, dtype=np.float32) for v in response.json()["vectors"]]
        
        similarity = np.dot(vecs[0], vecs[1])
        assert np.isclose(similarity, 1.0, atol=1e-6), f"Identical texts should have similarity 1.0, got {similarity}"

    def test_synonym_high_similarity(self, client):
        """Test that synonyms have high similarity scores"""
        synonyms = [
            ("big", "large"),
            ("small", "tiny"),
            ("happy", "joyful"),
            ("sad", "unhappy")
        ]
        
        for word1, word2 in synonyms:
            response = client.post("/embed", json={"texts": [word1, word2]})
            vecs = [np.array(v, dtype=np.float32) for v in response.json()["vectors"]]
            similarity = np.dot(vecs[0], vecs[1])
            
            # Synonyms should have similarity > 0.5
            assert similarity > 0.5, f"Synonyms '{word1}' and '{word2}' have low similarity: {similarity}"

    def test_antonym_lower_similarity(self, client):
        """Test that antonyms have lower similarity than synonyms"""
        word = "hot"
        synonym = "warm"
        antonym = "cold"
        
        response = client.post("/embed", json={"texts": [word, synonym, antonym]})
        vecs = [np.array(v, dtype=np.float32) for v in response.json()["vectors"]]
        
        similarity_synonym = np.dot(vecs[0], vecs[1])
        similarity_antonym = np.dot(vecs[0], vecs[2])
        
        assert similarity_synonym > similarity_antonym

    def test_unrelated_words_low_similarity(self, client):
        """Test that unrelated words have low similarity"""
        pairs = [
            ("three", "elephant"),
            ("hello", "mathematics"),
            ("red", "computer")
        ]
        
        for word1, word2 in pairs:
            response = client.post("/embed", json={"texts": [word1, word2]})
            vecs = [np.array(v, dtype=np.float32) for v in response.json()["vectors"]]
            similarity = np.dot(vecs[0], vecs[1])
            
            # Unrelated words should have similarity < 0.7
            assert similarity < 0.7, f"Unrelated '{word1}' and '{word2}' have high similarity: {similarity}"

    def test_similarity_symmetry(self, client):
        """Test that similarity is symmetric"""
        word1, word2 = "hello", "world"
        
        response = client.post("/embed", json={"texts": [word1, word2]})
        vecs = [np.array(v, dtype=np.float32) for v in response.json()["vectors"]]
        
        similarity_12 = np.dot(vecs[0], vecs[1])
        similarity_21 = np.dot(vecs[1], vecs[0])
        
        np.testing.assert_almost_equal(similarity_12, similarity_21, decimal=6)

    def test_batch_similarity_consistency(self, client):
        """Test that batch and individual embeddings produce same similarities"""
        words = ["three", "hello", "world"]
        
        # Batch
        batch_response = client.post("/embed", json={"texts": words})
        batch_vecs = [np.array(v, dtype=np.float32) for v in batch_response.json()["vectors"]]
        
        # Individual
        individual_vecs = []
        for word in words:
            response = client.post("/embed", json={"texts": [word]})
            individual_vecs.append(np.array(response.json()["vectors"][0], dtype=np.float32))
        
        # Compare similarities
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                batch_sim = np.dot(batch_vecs[i], batch_vecs[j])
                individual_sim = np.dot(individual_vecs[i], individual_vecs[j])
                np.testing.assert_almost_equal(batch_sim, individual_sim, decimal=5)


class TestSearchIntegration:
    """Integration tests for search service quality (requires search service running)"""

    @pytest.mark.integration
    def test_single_word_search_returns_results(self):
        """Test that single-word queries return search results"""
        # This would require the search service to be running
        # Marking as integration test
        pytest.skip("Requires running search service")

    @pytest.mark.integration  
    def test_search_score_ordering(self):
        """Test that search results are properly ordered by score"""
        pytest.skip("Requires running search service")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
