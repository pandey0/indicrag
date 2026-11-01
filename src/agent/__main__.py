"""python -m src.agent "I am 30 and live in Karnataka. Am I eligible for PM Jeevan Jyoti Bima Yojana?" [--chunks ...]

Needs ANTHROPIC_API_KEY (spends API budget). Prints the full JSON trace. Output is NOT an official eligibility decision.
"""
from __future__ import annotations

import argparse
import json

from src.evalrunner.run_retrieval import build_retriever, load_chunks
from src.generate.provider import AnthropicProvider

from .loop import run_agent
from .tools import ToolContext


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--chunks", default="data/chunks/fixed_512_64.jsonl")
    ap.add_argument("--max-steps", type=int, default=8)
    a = ap.parse_args()
    chunks = load_chunks(a.chunks)
    provider = AnthropicProvider()
    ctx = ToolContext(build_retriever("bm25", chunks, "", a.chunks), chunks, provider)
    print(json.dumps(run_agent(a.task, ctx, provider, max_steps=a.max_steps).trace(), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
