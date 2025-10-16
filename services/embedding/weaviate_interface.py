# services/embedding/weaviate_interface.py
import weaviate, os

client = weaviate.Client(
    url=os.environ.get("WEAVIATE_URL", "http://weaviate:8080"),
    additional_headers={"X-OpenAI-Api-Key": ""}  # not used
)

def upsert_batch(payloads, vectors_dict, class_name="Paragraph"):
    with client.batch as batch:
        batch.batch_size = 256
        for idx, payload in enumerate(payloads):
            vec = {name: vectors_dict[name][idx] for name in vectors_dict.keys()}
            client.batch.add_data_object(
                data_object=payload,
                class_name=class_name,
                uuid=payload["doc_id"],   # stable UUID (string allowed)
                vectors=vec
            )
