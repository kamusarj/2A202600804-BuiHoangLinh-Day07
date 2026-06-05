from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .agent import KnowledgeBaseAgent
from .chunking import RecursiveChunker
from .embeddings import _mock_embed
from .models import Document
from .store import EmbeddingStore

BENCHMARK_SCHEMA = {
    "embedding_models_comparison.md": {
        "category": "embedding",
        "language": "en",
        "difficulty": "advanced",
        "source": "technical-documentation",
    },
    "genAI.md": {
        "category": "generative-ai",
        "language": "en",
        "difficulty": "advanced",
        "source": "academic-paper",
    },
    "nlp_co_ban.md": {
        "category": "nlp",
        "language": "en",
        "difficulty": "intermediate",
        "source": "huggingface-course",
    },
    "prompt_engineering_fundamentals.txt": {
        "category": "prompt-engineering",
        "language": "vi",
        "difficulty": "intermediate",
        "source": "technical-guide",
    },
    "nist_generative_ai_profile.md": {
        "category": "ai-risk",
        "language": "en",
        "difficulty": "advanced",
        "source": "nist-framework",
    },
}


def parse_yaml_front_matter(text: str) -> dict:
    """Extract YAML front matter from text (simple parser)."""
    if text.startswith("---"):
        end = text.find("---", 4)
        if end != -1:
            fm = text[4:end].strip()
            result = {}
            for line in fm.split("\n"):
                kv = line.split(":", 1)
                if len(kv) == 2:
                    key = kv[0].strip()
                    val = kv[1].strip().strip('"').strip("'")
                    if val.startswith("[") and val.endswith("]"):
                        val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
                    result[key] = val
            return result
    return {}


def load_document(file_path: Path) -> Document | None:
    content = file_path.read_text(encoding="utf-8")
    yaml_meta = parse_yaml_front_matter(content)
    bench_meta = BENCHMARK_SCHEMA.get(file_path.name, {})

    if yaml_meta:
        title = yaml_meta.get("title", file_path.stem)
        content_body = content.split("---", 2)[-1] if content.startswith("---") else content
    else:
        title = file_path.stem
        content_body = content

    metadata = {
        **bench_meta,
        "title": title,
    }

    return Document(
        id=file_path.stem,
        content=content_body.strip(),
        metadata=metadata,
    )


def demo_llm(prompt: str) -> str:
    preview = prompt[:600].replace("\n", " ")
    return f"[LLM] Answer based on context: {preview}..."


def run_benchmark():
    data_dir = Path("data")
    files = sorted(data_dir.glob("*.md")) + sorted(data_dir.glob("*.txt"))
    existing = [f for f in files if f.name in BENCHMARK_SCHEMA]

    print("=" * 70)
    print("BENCHMARK: Retrieve Strategy — RecursiveChunker (chunk_size=1000)")
    print("=" * 70)
    print(f"\nLoading {len(existing)} documents:")

    docs = []
    for fp in existing:
        doc = load_document(fp)
        if doc:
            docs.append(doc)
            print(f"  [{doc.id}] {len(doc.content)} chars — {doc.metadata}")

    chunker = RecursiveChunker(chunk_size=1000)
    chunked_docs = []
    for doc in docs:
        chunks = chunker.chunk(doc.content)
        for i, chunk_text in enumerate(chunks):
            chunked_docs.append(
                Document(
                    id=f"{doc.id}_chunk{i}",
                    content=chunk_text,
                    metadata={**doc.metadata, "doc_id": doc.id, "chunk_index": i},
                )
            )

    print(f"\nTotal chunks: {len(chunked_docs)} (chunk_size=1000, recursive)")

    store = EmbeddingStore(collection_name="benchmark_store", embedding_fn=_mock_embed)
    store.add_documents(chunked_docs)
    print(f"Stored {store.get_collection_size()} records")

    queries = [
        {
            "query": "What are the dimensions and pricing of OpenAI text-embedding-3-large per 1K tokens?",
            "gold": "3,072 dimensions, $0.00013 per 1K tokens",
            "filter": None,
        },
        {
            "query": 'What is "Confabulation" according to NIST and how does it pose risks in healthcare?',
            "gold": "Confabulation is GAI generating and confidently presenting erroneous/false content. In healthcare, could cause wrong diagnoses and treatments.",
            "filter": None,
        },
        {
            "query": "What are the main features of the Hugging Face Transformers library?",
            "gold": "Ease of use (2 lines of code), Flexibility (PyTorch nn.Module), Simplicity (All in one file)",
            "filter": None,
        },
        {
            "query": "Kỹ thuật Chain-of-Thought (CoT) Prompting hoạt động như thế nào và tại sao nó giúp giảm hallucination?",
            "gold": "CoT yêu cầu mô hình trình bày từng bước suy luận logic trước khi kết luận, giúp giảm hallucination.",
            "filter": None,
        },
        {
            "query": "Find the AI risk management framework developed by a US government organization. List 5 main risks of Generative AI according to NIST.",
            "gold": "NIST AI 600-1, 5 risks: CBRN, Confabulation, Dangerous Content, Data Privacy, Environmental",
            "filter": {"source": "nist-framework"},
        },
    ]

    print("\n" + "=" * 70)
    print("QUERY RESULTS")
    print("=" * 70)

    for i, q in enumerate(queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Query: {q['query']}")
        print(f"Gold:  {q['gold']}")
        print(f"Filter: {q.get('filter')}")

        if q.get("filter"):
            results = store.search_with_filter(q["query"], top_k=3, metadata_filter=q["filter"])
        else:
            results = store.search(q["query"], top_k=3)

        for j, r in enumerate(results, 1):
            preview = r["content"][:150].replace("\n", " ")
            print(f"  [{j}] score={r['score']:.4f} | doc={r['metadata'].get('doc_id', '?')}")
            print(f"      content: {preview}...")

    print("\n" + "=" * 70)
    print("KNOWLEDGE BASE AGENT TEST")
    print("=" * 70)
    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
    for i, q in enumerate(queries, 1):
        if i == 5:
            continue
        print(f"\n--- Agent Answer {i} ---")
        print(f"Q: {q['query']}")
        ans = agent.answer(q["query"], top_k=3)
        print(f"A: {ans[:300]}...")


if __name__ == "__main__":
    run_benchmark()
