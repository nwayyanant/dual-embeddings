# services/ingestion/etl.py
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List
from .io import strip_diacritics, normalize_nfc

def _first_existing(chunk: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in chunk.columns:
            return c
    return None

def run_etl(csv_path: str, out_parquet: str, schema_cfg: Optional[Dict] = None) -> dict:
    """
    Flexible ETL:
      - Detects id fields and text fields using provided schema config (aliases).
      - Normalizes NFC and creates *_ascii for any text field we keep.
      - Builds multilingual_concat in the order given, using existing fields only.
      - Allows replacing CSV with new columns without code changes.
    """
    print(f"[ETL] Starting ETL for: {csv_path}")

    csv_path = Path(csv_path)
    assert csv_path.exists(), f"CSV not found: {csv_path}"

    cfg = schema_cfg or {}
    id_fields: List[str] = cfg.get("id_fields", ["book_id","para_id"])
    aliases: Dict[str, List[str]] = cfg.get("text_field_aliases", {
        "pali": ["pali_paragraph", "pali_text"],
        "en":   ["translation_paragraph", "english_paragraph", "en_paragraph"],
        "zh":   ["chinese_paragraph", "zh_paragraph"],
        "ru":   ["russian_paragraph", "ru_paragraph"]
    })
    concat_order: List[str] = cfg.get("concat_order", ["pali","en","zh","ru"])

    if not isinstance(id_fields, list) or not all(isinstance(f, str) for f in id_fields):
        raise ValueError("Invalid schema: 'id_fields' must be a list of strings")

    CHUNK = 200_000
    rows = []
    selected_cols = []  # remember which actual columns we used

    for chunk in pd.read_csv(csv_path, dtype=str, chunksize=CHUNK):
        # Validate id fields
        for fid in id_fields:
            if fid not in chunk.columns:
                raise ValueError(f"CSV missing required id field: {fid}")

        # Resolve actual text columns from aliases
        resolved: Dict[str, Optional[str]] = {}
        for canon, cands in aliases.items():
            resolved[canon] = _first_existing(chunk, cands)

        # Normalize all resolved text columns and create *_ascii
        for canon, actual_col in resolved.items():
            if actual_col:
                chunk[actual_col] = chunk[actual_col].map(normalize_nfc)
                # chunk[f"{actual_col}_ascii"] = chunk[actual_col].map(strip_diacritics)
                selected_cols.append(actual_col)

        ascii_cols = [col for col in chunk.columns if col.endswith("_ascii")]
        chunk.drop(columns=ascii_cols, inplace=True)

        # doc_id (stable)
        chunk["doc_id"] = chunk[id_fields[0]].astype(str)
        for extra in id_fields[1:]:
            chunk["doc_id"] = chunk["doc_id"] + ":" + chunk[extra].astype(str)

        # Dedup
        dedup_cols = ["doc_id"] + [resolved[k] for k in resolved if resolved[k]]
        chunk = chunk.drop_duplicates(subset=dedup_cols)

        # multilingual_concat in requested order (only existing)
        concat_actual = [resolved[key] for key in concat_order if resolved.get(key)]
        
        # If no canonical matched (edge case), fallback to any string columns excluding ids
        if not concat_actual:
            print("[ETL] Warning: No canonical text columns found. Falling back to any string columns.")
            concat_actual = [
                c for c in chunk.columns
                if c not in id_fields and not c.endswith("_ascii") and chunk[c].dtype == "object"
            ]

        chunk["multilingual_concat"] = chunk[concat_actual].fillna("").agg(" \n ".join, axis=1)

        # Keep also a normalized "pali_paragraph" and "translation_paragraph" if present so downstream UI sees them
        # Find best match for pali/en
        pali_col = resolved.get("pali")
        en_col = resolved.get("en")
        if pali_col and pali_col != "pali_paragraph":
            chunk["pali_paragraph"] = chunk[pali_col]
            # chunk["pali_paragraph_ascii"] = chunk[f"{pali_col}_ascii"]
        if en_col and en_col != "translation_paragraph":
            chunk["translation_paragraph"] = chunk[en_col]
            # chunk["translation_paragraph_ascii"] = chunk[f"{en_col}_ascii"]

        rows.append(chunk)

    df = pd.concat(rows, ignore_index=True)

    out = Path(out_parquet)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)

    return {
        "rows": len(df),
        "parquet": str(out),
        "used_text_columns": sorted(set(selected_cols)),
        "id_fields": id_fields
    }