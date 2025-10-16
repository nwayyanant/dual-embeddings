# services/search/language.py
import unicodedata, re

def strip_diacritics(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def detect_lang(q: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", q): return "zh"
    if re.search(r"[\u0400-\u04FF]", q): return "ru"
    if re.search(r"[āīūḍḷṇṭñĀĪŪḌḶṆṬÑ]", q): return "pali"
    # crude default
    return "en"