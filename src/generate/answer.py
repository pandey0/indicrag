"""RAG answering with citation validation and refusal (docs/15, docs/11 s2)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from .provider import Completion, LLMProvider

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "answer.v1.txt"
LANG_NAME = {"en": "English", "hi": "Hindi (Devanagari)", "kn": "Kannada"}
REFUSAL = {
    "en": "I could not find this in the available documents, so I can't answer it reliably. Please check the official government website or office.",
    "hi": "मुझे उपलब्ध दस्तावेज़ों में इसका उत्तर नहीं मिला, इसलिए मैं भरोसे से नहीं बता सकता। कृपया आधिकारिक सरकारी वेबसाइट या कार्यालय से पुष्टि करें।",
    "kn": "ಲಭ್ಯವಿರುವ ದಾಖಲೆಗಳಲ್ಲಿ ಇದಕ್ಕೆ ಉತ್ತರ ಸಿಗಲಿಲ್ಲ, ಆದ್ದರಿಂದ ವಿಶ್ವಾಸಾರ್ಹವಾಗಿ ಹೇಳಲು ಸಾಧ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಜಾಲತಾಣ ಅಥವಾ ಕಚೇರಿಯನ್ನು ಪರಿಶೀಲಿಸಿ.",
}
CITE = re.compile(r"\[c(\d+)\]")


def detect_lang(text: str) -> str:
    """Majority-script language of the question (code-mixed -> majority script; default en)."""
    dev = sum(0x0900 <= ord(c) <= 0x097F for c in text)
    kan = sum(0x0C80 <= ord(c) <= 0x0CFF for c in text)
    lat = sum(c.isascii() and c.isalpha() for c in text)
    best = max((dev, "hi"), (kan, "kn"), (lat, "en"))
    return best[1]


def prompt_template() -> tuple[str, str]:
    t = PROMPT_PATH.read_text(encoding="utf-8")
    return t, hashlib.sha256(t.encode()).hexdigest()[:12]


@dataclass
class Source:
    cid: str            # context id shown to the model, e.g. "c1"
    chunk_id: str
    doc_id: str
    text: str


@dataclass
class Answer:
    text: str
    lang: str
    refused: bool
    reason: str                      # "" | no_retrieval | low_score | model_no_answer | invalid_citation | uncited
    sources: list[Source] = field(default_factory=list)   # all passages shown to the model
    cited: list[str] = field(default_factory=list)        # context ids actually cited
    prompt_hash: str = ""
    completion: Completion | None = None


def build_context(hits_text: list[tuple[str, str, str]], max_chars: int = 1800) -> tuple[str, list[Source]]:
    """hits_text: (chunk_id, doc_id, text). Passages are delimited data blocks, each capped in length."""
    srcs, blocks = [], []
    for i, (chunk_id, doc_id, text) in enumerate(hits_text, 1):
        cid = f"c{i}"
        srcs.append(Source(cid, chunk_id, doc_id, text))
        blocks.append(f'<passage id="{cid}">\n{text[:max_chars]}\n</passage>')
    return "\n".join(blocks), srcs


def answer_question(question: str, retriever, chunks: dict[str, dict], provider: LLMProvider, k: int = 5,
                    min_score: float = 0.0, max_tokens: int = 400) -> Answer:
    lang = detect_lang(question)
    template, phash = prompt_template()
    hits = retriever.search(question, k)
    if not hits:
        return Answer(REFUSAL[lang], lang, True, "no_retrieval", prompt_hash=phash)
    if hits[0].score < min_score:
        return Answer(REFUSAL[lang], lang, True, "low_score", prompt_hash=phash)
    context, srcs = build_context([(h.chunk_id, chunks[h.chunk_id]["doc_id"], chunks[h.chunk_id]["text"]) for h in hits])
    system = template.format(lang_name=LANG_NAME[lang])
    user = f"{context}\n\nQuestion: {question}"
    comp = provider.complete(system, user, max_tokens)
    out = comp.text.strip()
    if out.startswith("NO_ANSWER"):
        return Answer(REFUSAL[lang], lang, True, "model_no_answer", srcs, [], phash, comp)
    cited = CITE.findall(out)
    valid = {s.cid for s in srcs}
    ids = [f"c{n}" for n in cited]
    if any(i not in valid for i in ids):
        return Answer(REFUSAL[lang], lang, True, "invalid_citation", srcs, [], phash, comp)
    if not ids:
        return Answer(REFUSAL[lang], lang, True, "uncited", srcs, [], phash, comp)
    return Answer(out, lang, False, "", srcs, sorted(set(ids), key=lambda x: int(x[1:])), phash, comp)
