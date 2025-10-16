# this may be unused file, to delete it later.
import os
import weaviate

CLASS = "Paragraph"

def ensure_schema(client: weaviate.Client, named_vectors: bool=False):
    """
    Create Weaviate class:
      - by default: SINGLE 'multilingual' vector (compat across Weaviate versions)
      - optional: named vectors ('pali','en','multilingual') when named_vectors=True

    NOTE: We use external vectors (vectorizer='none') and Weaviate's BM25 module for keyword.
    """
    schema = client.schema.get()
    classes = {c["class"] for c in schema.get("classes", [])}
    if CLASS in classes:
        return

    base_props = [
        {"name":"doc_id","dataType":["text"],"indexInverted":True},
        {"name":"book_id","dataType":["text"],"indexInverted":True},
        {"name":"para_id","dataType":["text"],"indexInverted":True},

        {"name":"pali_paragraph","dataType":["text"],"indexInverted":True},
        {"name":"pali_paragraph_ascii","dataType":["text"],"indexInverted":True},

        {"name":"translation_paragraph","dataType":["text"],"indexInverted":True},
        {"name":"translation_paragraph_ascii","dataType":["text"],"indexInverted":True},

        {"name":"multilingual_concat","dataType":["text"],"indexInverted":True},
    ]

    # Simple, compatible schema: single vector
    class_obj = {
        "class": CLASS,
        "description": "Pali & English paragraphs",
        "vectorizer": "none",   # external embeddings
        "vectorIndexType": "hnsw",
        "vectorIndexConfig": {
            "distance": "cosine",
            "efConstruction": 128,
            "maxConnections": 64
        },
        "properties": base_props
    }

    # NOTE: If you later upgrade and want named vectors,
    # you can adapt to Weaviate's "vectorConfig" per-vector block.
    client.schema.create_class(class_obj)