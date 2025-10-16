import os
from typing import List, Dict

class LLMProvider:
    def __init__(self):
        self.name = os.getenv("LLM_PROVIDER", "none")

    def generate(self, prompt: str, temperature: float=0.2, max_tokens: int=600) -> str:
        if self.name == "none":
            # When disabled, caller will use make_bilingual_answer(...)
            return "LLM disabled."
        # TODO: Implement provider call (Azure/OpenAI/local) when enabled
        return "TODO: Implement LLM provider call."

def build_prompt(query: str, contexts: List[Dict], target_lang: str) -> str:
    blocks = []
    for c in contexts:
        cite = f"[{c.get('book_id','?')}:{c.get('para_id','?')}]"
        text_parts = [c.get("pali_paragraph"), c.get("translation_paragraph")]
        text = " / ".join([t for t in text_parts if t])
        blocks.append(f"{cite} {text}")
    ctx = "\n\n".join(blocks)
    return f"""Answer in {target_lang}. Use only the context and cite [book_id:para_id].

Question: {query}

Context:
{ctx}
"""

def make_bilingual_answer(query: str, contexts: List[Dict], target_lang: str, max_summary_chars: int = 600, max_blocks: int = 6) -> str:
    """
    Build a readable, extractive bilingual answer with citations even when no LLM is available.
    - Pāli-first if target_lang == 'pali'; English-first otherwise.
    - Summarizes by stitching the first few relevant English lines (fallback to Pāli).
    - Always prints citations [book_id:para_id].
    """
    if not contexts:
        return f"No matching passages found for: {query}"

    # Choose display order
    first_key, second_key = ("pali_paragraph", "translation_paragraph") if target_lang == "pali" else ("translation_paragraph", "pali_paragraph")

    # Simple extractive "summary": take English lines (or Pāli if missing) from top contexts
    summary_parts = []
    for c in contexts[:max_blocks]:
        primary = (c.get("translation_paragraph") or c.get("pali_paragraph") or "").strip()
        if primary:
            summary_parts.append(primary)
        if sum(len(x) for x in summary_parts) >= max_summary_chars:
            break
    summary_text = " ".join(summary_parts)
    if len(summary_text) > max_summary_chars:
        summary_text = summary_text[:max_summary_chars].rsplit(" ", 1)[0] + "…"

    # Build citations block with bilingual lines
    cite_blocks = []
    for c in contexts[:max_blocks]:
        cite = f"[{c.get('book_id','?')}:{c.get('para_id','?')}]"
        line_first  = (c.get(first_key)  or "").strip()
        line_second = (c.get(second_key) or "").strip()
        if line_first or line_second:
            cite_blocks.append(f"{cite}\n{line_first}\n{line_second}\n")

    # Compose final answer
    header = "Extractive bilingual answer (context-stitched)"
    return f"{header}\n\nSummary:\n{summary_text}\n\nCitations:\n" + "\n".join(cite_blocks)