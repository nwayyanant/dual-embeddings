# services/embedding/worker.py
import pandas as pd
from model import LabseEncoder
from weaviate_interface import upsert_batch

def build_multilingual_text(row):
    parts = []
    for col in ["pali_paragraph","english_paragraph","chinese_paragraph","russian_paragraph"]:
        if col in row and isinstance(row[col], str) and row[col]:
            parts.append(row[col])
    return " \n ".join(parts) if parts else ""

def process_parquet(parquet_path: str, batch_size=5000):
    df = pd.read_parquet(parquet_path)
    enc = LabseEncoder()

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size].copy()

        vectors = {}
        # Create per-language vectors if text exists
        if "pali_paragraph" in df.columns:
            vectors["pali"] = enc.encode(batch["pali_paragraph"].fillna("").tolist())
        if "english_paragraph" in df.columns:
            vectors["en"] = enc.encode(batch["english_paragraph"].fillna("").tolist())
        if "chinese_paragraph" in df.columns:
            vectors["zh"] = enc.encode(batch["chinese_paragraph"].fillna("").tolist())
        if "russian_paragraph" in df.columns:
            vectors["ru"] = enc.encode(batch["russian_paragraph"].fillna("").tolist())

        # Multilingual fused
        ml_texts = batch.apply(build_multilingual_text, axis=1).tolist()
        vectors["multilingual"] = enc.encode(ml_texts)

        payloads = []
        for j, row in batch.iterrows():
            payload = {
                "doc_id": row["doc_id"],
                "book_id": row["book_id"],
                "para_id": row["para_id"],
                "pali_paragraph": row.get("pali_paragraph"),
                "pali_paragraph_ascii": row.get("pali_paragraph_ascii"),
                "english_paragraph": row.get("english_paragraph"),
                "english_paragraph_ascii": row.get("english_paragraph_ascii"),
                "chinese_paragraph": row.get("chinese_paragraph"),
                "russian_paragraph": row.get("russian_paragraph"),
                "multilingual_concat": row.get("multilingual_concat"),
            }
            payloads.append(payload)

        # Upsert to Weaviate with named vectors
        upsert_batch(payloads, vectors)
