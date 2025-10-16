# services/search/weaviate_client.py
import weaviate, os

client = weaviate.Client(os.environ.get("WEAVIATE_URL","http://weaviate:8080"))
CLASS = "Paragraph"

def hybrid_search(query_text: str, vector: list[float] | None, vector_name: str, alpha=0.5, limit=100, filters=None):
    """
    alpha: 0.0 -> pure keyword, 1.0 -> pure vector
    """
    q = (
      client.query
        .get(CLASS, ["doc_id","book_id","para_id","pali_paragraph","english_paragraph","chinese_paragraph","russian_paragraph"])
        .with_hybrid(query=query_text, alpha=alpha, vector=vector, vector_properties=[vector_name] if vector else None)
        .with_limit(limit)
    )
    if filters:
        q = q.with_where(filters)
    return q.do()