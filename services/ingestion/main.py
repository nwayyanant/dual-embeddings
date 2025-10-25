# services/ingestion/main.py

# This code defines a FastAPI-based ingestion service 
# for processing multilingual CSV files
#  (e.g., Pali-English texts) and converting them into 
# normalized Parquet format using a configurable schema.

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from .etl import run_etl

app = FastAPI(title="Pali/English Ingestion Service")

DEFAULT_SCHEMA = {
    "id_fields": ["book_id", "para_id"],
    "text_field_aliases": {
        "pali": ["pali_paragraph"],
        "en": ["translation_paragraph"]
    },
    "concat_order": ["pali", "en"]
}
class SchemaConfig(BaseModel):
    id_fields: List[str] = ["book_id", "para_id"]
    # canonical -> list of candidate column names (first found will be used)
    text_field_aliases: Dict[str, List[str]] = {
        "pali": ["pali_paragraph", "pali_text"],
        "en":   ["translation_paragraph", "english_paragraph", "en_paragraph"],
        "zh":   ["chinese_paragraph", "zh_paragraph"],
        "ru":   ["russian_paragraph", "ru_paragraph"]
    }
    # order in which to concatenate (only existing ones are used)
    concat_order: List[str] = ["pali","en","zh","ru"]

class IngestBody(BaseModel):
    csv_path: str = Field(..., description="Path to input CSV")
    out_parquet: str = Field(..., description="Path to write normalized parquet")
    schema: Optional[SchemaConfig] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"service": "ingestion", "status": "ok"}

@app.post("/ingest")
def ingest(body: IngestBody):
    cfg = body.schema.dict() if body.schema else DEFAULT_SCHEMA
    result = run_etl(body.csv_path, body.out_parquet, cfg)
    return {"message": "ETL completed", **result}