import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import httpx

from services.search.main import (
    app,
    build_snippet,
    get_query_vector,
)


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_weaviate_results():
    """Sample Weaviate search results"""
    return {
        "data": {
            "Get": {
                "Paragraph": [
                    {
                        "doc_id": "doc_1",
                        "book_id": "book_1",
                        "para_id": "p1",
                        "pali_paragraph": "Sabbadānaṃ dhammadānaṃ jināti",
                        "translation_paragraph": "The gift of Dhamma surpasses all gifts",
                    },
                    {
                        "doc_id": "doc_2",
                        "book_id": "book_1",
                        "para_id": "p2",
                        "pali_paragraph": "Sabbe dhammā nālaṃ abhinivesāya",
                        "translation_paragraph": "Nothing is worth clinging to",
                    },
                    {
                        "doc_id": "doc_3",
                        "book_id": "book_2",
                        "para_id": "p3",
                        "pali_paragraph": "Appamādo amatapadaṃ",
                        "translation_paragraph": "Heedfulness is the path to the deathless",
                    },
                ]
            }
        }
    }


@pytest.fixture
def sample_embedding_response():
    """Sample embedding service response"""
    return {
        "vectors": [
            [0.1] * 768  # Mock 768-dim vector
        ]
    }


class TestBuildSnippet:
    """Tests for build_snippet function"""

    def test_build_snippet_with_both_fields(self):
        """Test building snippet with both pali and translation"""
        obj = {
            "pali_paragraph": "Pali text here",
            "translation_paragraph": "Translation text here",
        }
        result = build_snippet(obj)
        assert "Pali text here" in result
        assert "Translation text here" in result
        assert " \n " in result

    def test_build_snippet_with_only_pali(self):
        """Test building snippet with only pali"""
        obj = {
            "pali_paragraph": "Pali text only",
            "translation_paragraph": None,
        }
        result = build_snippet(obj)
        assert "Pali text only" in result
        assert result == "Pali text only"

    def test_build_snippet_with_only_translation(self):
        """Test building snippet with only translation"""
        obj = {
            "pali_paragraph": None,
            "translation_paragraph": "Translation only",
        }
        result = build_snippet(obj)
        assert "Translation only" in result

    def test_build_snippet_with_missing_fields(self):
        """Test building snippet with missing fields"""
        obj = {}
        result = build_snippet(obj)
        assert result == ""


class TestGetQueryVector:
    """Tests for get_query_vector function"""

    @pytest.mark.asyncio
    async def test_get_query_vector_success(self, sample_embedding_response):
        """Test successful vector retrieval"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_embedding_response
            mock_response.raise_for_status = Mock()
            
            mock_session = AsyncMock()
            mock_session.post.return_value = mock_response
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_client.return_value = mock_session

            result = await get_query_vector("hello")
            
            assert result is not None
            assert len(result) == 768
            assert all(isinstance(x, (int, float)) for x in result)

    @pytest.mark.asyncio
    async def test_get_query_vector_http_error(self):
        """Test graceful degradation on HTTP error"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPError("Error")
            
            mock_session = AsyncMock()
            mock_session.post.return_value = mock_response
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_client.return_value = mock_session

            result = await get_query_vector("test query")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_query_vector_empty_response(self):
        """Test handling of empty vectors in response"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"vectors": []}
            mock_response.raise_for_status = Mock()
            
            mock_session = AsyncMock()
            mock_session.post.return_value = mock_response
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_client.return_value = mock_session

            result = await get_query_vector("test query")
            
            assert result is None


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
        assert data["service"] == "search"
        assert data["status"] == "ok"
        assert "embedding_url" in data


class TestSearchEndpoint:
    """Tests for /search endpoint"""

    @patch("services.search.main.client")
    @patch("services.search.main.get_query_vector")
    @patch("services.search.main.detect_lang")
    @patch("services.search.main.reranker")
    def test_search_basic_query(
        self, mock_reranker, mock_detect_lang, mock_get_vector, mock_weaviate, client, sample_weaviate_results
    ):
        """Test basic search query"""
        # Setup mocks
        mock_detect_lang.return_value = "en"
        mock_get_vector.return_value = [0.1] * 768
        
        mock_query = MagicMock()
        mock_query.with_hybrid.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.do.return_value = sample_weaviate_results
        
        mock_weaviate.query.get.return_value = mock_query
        
        # Mock reranker to assign descending scores
        def mock_rerank(query, hits, text_key, top_k):
            for i, hit in enumerate(hits[:top_k]):
                hit["_rerank_score"] = 1.0 - (i * 0.1)  # 1.0, 0.9, 0.8, etc.
            return hits[:top_k]
        
        mock_reranker.rerank.side_effect = mock_rerank

        response = client.post("/search", json={"query": "dhamma gift", "top_k": 3})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) <= 3
        assert "query_lang" in data
        assert data["query_lang"] == "en"

    @patch("services.search.main.client")
    @patch("services.search.main.get_query_vector")
    @patch("services.search.main.detect_lang")
    @patch("services.search.main.reranker")
    def test_search_scores_closest_to_one(
        self, mock_reranker, mock_detect_lang, mock_get_vector, mock_weaviate, client, sample_weaviate_results
    ):
        """Test that the most relevant results have scores closest to 1"""
        # Setup mocks
        mock_detect_lang.return_value = "en"
        mock_get_vector.return_value = [0.1] * 768
        
        mock_query = MagicMock()
        mock_query.with_hybrid.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.do.return_value = sample_weaviate_results
        
        mock_weaviate.query.get.return_value = mock_query
        
        # Mock reranker to return realistic scores
        def mock_rerank(query, hits, text_key, top_k):
            # Simulate reranking with decreasing scores
            scores = [0.95, 0.87, 0.72, 0.58, 0.45]
            for i, hit in enumerate(hits[:top_k]):
                hit["_rerank_score"] = scores[i] if i < len(scores) else 0.1
            return hits[:top_k]
        
        mock_reranker.rerank.side_effect = mock_rerank

        response = client.post("/search", json={"query": "test query", "top_k": 5})
        
        assert response.status_code == 200
        data = response.json()
        results = data["results"]
        
        # Verify scores exist and are in descending order
        assert len(results) > 0
        scores = [r["score"] for r in results]
        
        # First result should have highest score
        assert scores[0] == max(scores)
        
        # First score should be closest to 1
        assert scores[0] >= 0.9
        assert scores[0] <= 1.0
        
        # Scores should be in descending order
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"Scores not in descending order: {scores}"

    @patch("services.search.main.client")
    @patch("services.search.main.get_query_vector")
    @patch("services.search.main.detect_lang")
    @patch("services.search.main.reranker")
    def test_search_score_range(
        self, mock_reranker, mock_detect_lang, mock_get_vector, mock_weaviate, client, sample_weaviate_results
    ):
        """Test that scores are within valid range (0 to 1)"""
        mock_detect_lang.return_value = "en"
        mock_get_vector.return_value = [0.1] * 768
        
        mock_query = MagicMock()
        mock_query.with_hybrid.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.do.return_value = sample_weaviate_results
        
        mock_weaviate.query.get.return_value = mock_query
        
        def mock_rerank(query, hits, text_key, top_k):
            for i, hit in enumerate(hits[:top_k]):
                hit["_rerank_score"] = 0.9 - (i * 0.15)
            return hits[:top_k]
        
        mock_reranker.rerank.side_effect = mock_rerank

        response = client.post("/search", json={"query": "test", "top_k": 5})
        data = response.json()
        
        for result in data["results"]:
            score = result["score"]
            assert 0.0 <= score <= 1.0, f"Score {score} out of valid range [0, 1]"

    @patch("services.search.main.client")
    @patch("services.search.main.get_query_vector")
    @patch("services.search.main.detect_lang")
    @patch("services.search.main.strip_diacritics")
    @patch("services.search.main.reranker")
    def test_search_pali_language_detection(
        self, mock_reranker, mock_strip, mock_detect_lang, mock_get_vector, mock_weaviate, client, sample_weaviate_results
    ):
        """Test search with Pali language detection"""
        mock_detect_lang.return_value = "pali"
        mock_strip.return_value = "stripped pali text"
        mock_get_vector.return_value = [0.1] * 768
        
        mock_query = MagicMock()
        mock_query.with_hybrid.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.do.return_value = sample_weaviate_results
        
        mock_weaviate.query.get.return_value = mock_query
        
        def mock_rerank(query, hits, text_key, top_k):
            for i, hit in enumerate(hits[:top_k]):
                hit["_rerank_score"] = 0.85
            return hits[:top_k]
        
        mock_reranker.rerank.side_effect = mock_rerank

        response = client.post("/search", json={"query": "sabbadānaṃ", "top_k": 3})
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_lang"] == "pali"
        
        # Verify strip_diacritics was called for Pali text
        mock_strip.assert_called_once()

    @patch("services.search.main.client")
    @patch("services.search.main.get_query_vector")
    @patch("services.search.main.detect_lang")
    @patch("services.search.main.reranker")
    def test_search_bm25_fallback(
        self, mock_reranker, mock_detect_lang, mock_get_vector, mock_weaviate, client, sample_weaviate_results
    ):
        """Test BM25-only fallback when vector embedding fails"""
        mock_detect_lang.return_value = "en"
        mock_get_vector.return_value = None  # Simulate embedding failure
        
        mock_query = MagicMock()
        mock_query.with_hybrid.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.do.return_value = sample_weaviate_results
        
        mock_weaviate.query.get.return_value = mock_query
        
        def mock_rerank(query, hits, text_key, top_k):
            for i, hit in enumerate(hits[:top_k]):
                hit["_rerank_score"] = 0.7
            return hits[:top_k]
        
        mock_reranker.rerank.side_effect = mock_rerank

        response = client.post("/search", json={"query": "test", "top_k": 3, "alpha": 0.5})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify alpha was set to 0.0 for BM25-only
        assert data["alpha"] == 0.0

    @patch("services.search.main.client")
    @patch("services.search.main.get_query_vector")
    @patch("services.search.main.detect_lang")
    @patch("services.search.main.reranker")
    def test_search_vector_only_fallback(
        self, mock_reranker, mock_detect_lang, mock_get_vector, mock_weaviate, client
    ):
        """Test vector-only fallback when hybrid search returns empty"""
        mock_detect_lang.return_value = "en"
        mock_get_vector.return_value = [0.1] * 768
        
        # First query returns empty, second returns results
        empty_result = {"data": {"Get": {"Paragraph": []}}}
        filled_result = {
            "data": {
                "Get": {
                    "Paragraph": [
                        {
                            "doc_id": "doc_1",
                            "book_id": "book_1",
                            "para_id": "p1",
                            "pali_paragraph": "Test",
                            "translation_paragraph": "Test translation",
                        }
                    ]
                }
            }
        }
        
        mock_query = MagicMock()
        mock_query.with_hybrid.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.do.side_effect = [empty_result, filled_result]
        
        mock_weaviate.query.get.return_value = mock_query
        
        def mock_rerank(query, hits, text_key, top_k):
            for hit in hits[:top_k]:
                hit["_rerank_score"] = 0.8
            return hits[:top_k]
        
        mock_reranker.rerank.side_effect = mock_rerank

        response = client.post("/search", json={"query": "test", "top_k": 5})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0


class TestAnswerEndpoint:
    """Tests for /answer endpoint"""

    @patch("services.search.main.search")
    @patch("services.search.main.llm")
    def test_answer_with_llm(self, mock_llm, mock_search, client):
        """Test answer generation with LLM"""
        # Mock search results
        mock_search.return_value = {
            "results": [
                {
                    "snippet": "Test snippet 1",
                    "score": 0.95,
                    "doc_id": "doc_1",
                },
                {
                    "snippet": "Test snippet 2",
                    "score": 0.85,
                    "doc_id": "doc_2",
                },
            ],
            "query_lang": "en",
        }
        
        mock_llm.name = "test-llm"
        mock_llm.generate.return_value = "Generated answer from LLM"

        response = client.post("/answer", json={"query": "What is dhamma?", "top_k": 5})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "citations" in data
        assert data["lang"] == "en"
        assert len(data["citations"]) <= 10

    @patch("services.search.main.search")
    @patch("services.search.main.llm")
    @patch("services.search.main.make_bilingual_answer")
    def test_answer_without_llm(self, mock_bilingual, mock_llm, mock_search, client):
        """Test answer generation without LLM (fallback)"""
        mock_search.return_value = {
            "results": [{"snippet": "Test", "score": 0.9, "doc_id": "doc_1"}],
            "query_lang": "en",
        }
        
        mock_llm.name = "none"
        mock_bilingual.return_value = "Bilingual answer"

        response = client.post("/answer", json={"query": "test", "top_k": 3})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["answer"] == "Bilingual answer"
        mock_bilingual.assert_called_once()


class TestIntegration:
    """Integration tests"""

    @patch("services.search.main.client")
    @patch("services.search.main.get_query_vector")
    @patch("services.search.main.detect_lang")
    @patch("services.search.main.reranker")
    def test_search_to_answer_flow(
        self, mock_reranker, mock_detect_lang, mock_get_vector, mock_weaviate, client, sample_weaviate_results
    ):
        """Test complete search to answer flow"""
        mock_detect_lang.return_value = "en"
        mock_get_vector.return_value = [0.1] * 768
        
        mock_query = MagicMock()
        mock_query.with_hybrid.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.do.return_value = sample_weaviate_results
        
        mock_weaviate.query.get.return_value = mock_query
        
        def mock_rerank(query, hits, text_key, top_k):
            for i, hit in enumerate(hits[:top_k]):
                hit["_rerank_score"] = 0.9 - (i * 0.1)
            return hits[:top_k]
        
        mock_reranker.rerank.side_effect = mock_rerank

        # First do search
        search_response = client.post("/search", json={"query": "dhamma", "top_k": 3})
        assert search_response.status_code == 200
        
        # Verify we can use search results
        search_data = search_response.json()
        assert len(search_data["results"]) > 0
        assert all("score" in r for r in search_data["results"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
