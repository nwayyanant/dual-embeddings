# services/embedding/weaviate_schema.py
import weaviate
import os

CLASS = "Paragraph"
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")

def ensure_schema(client: weaviate.Client, named_vectors: bool = False):
    """
    Create the Weaviate class for our data:
      - By default: a SINGLE 'multilingual' external vector (vectorizer='none')
      - Optional 'named_vectors' is kept for future use (not enabled in this MVP)

    We rely on external embeddings (LaBSE) and Weaviate's BM25 module for hybrid search.
    """
    schema = client.schema.get()
    existing = {c["class"] for c in schema.get("classes", [])}
    if CLASS in existing:
        return  # already present

    base_props = [
        {"name": "doc_id", "dataType": ["text"], "indexInverted": True},
        {"name": "book_id", "dataType": ["text"], "indexInverted": True},
        {"name": "para_id", "dataType": ["text"], "indexInverted": True},

        {"name": "pali_paragraph", "dataType": ["text"], "indexInverted": True},
        {"name": "pali_paragraph_ascii", "dataType": ["text"], "indexInverted": True},

        {"name": "translation_paragraph", "dataType": ["text"], "indexInverted": True},
        {"name": "translation_paragraph_ascii", "dataType": ["text"], "indexInverted": True},

        {"name": "multilingual_concat", "dataType": ["text"], "indexInverted": True},
    ]

    class_obj = {
        "class": CLASS,
        "description": "Pali & English paragraphs (external vectors + BM25)",
        "vectorizer": "none",          # we push external vectors
        "vectorIndexType": "hnsw",
        "vectorIndexConfig": {
            "distance": "cosine",
            "efConstruction": 128,
            "maxConnections": 64,
        },
        "properties": base_props,
    }

    # NOTE: If you later upgrade Weaviate and want named vectors,
    # you'll adapt this to the per-vector "vectorConfig" blocks.
    client.schema.create_class(class_obj)

if __name__ == "__main__":
    print("Connecting to Weaviate...")
    client = weaviate.Client(WEAVIATE_URL)
    ensure_schema(client)
    print("Schema setup complete.")