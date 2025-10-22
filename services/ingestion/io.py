import unicodedata
from typing import Optional
def strip_diacritics(s: Optional[str]) -> Optional[str]:
    """Remove diacritical marks from a Unicode string using NFKD normalization."""
    if not s:
        return s
    nfkd = unicodedata.normalize("NFKD", s)
    return ''.join(ch for ch in nfkd if not unicodedata.combining(ch))

def normalize_nfc(s: Optional[str]) -> Optional[str]:
    """Normalize a Unicode string to NFC form and strip surrounding whitespace."""
    if not s:
        return s
    return unicodedata.normalize("NFC", s).strip()