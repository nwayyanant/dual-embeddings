import unicodedata
from typing import Optional

def strip_diacritics(s: Optional[str]) -> Optional[str]:
    if s is None: return s
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def normalize_nfc(s: Optional[str]) -> Optional[str]:
    if s is None: return s
    return unicodedata.normalize("NFC", s).strip()