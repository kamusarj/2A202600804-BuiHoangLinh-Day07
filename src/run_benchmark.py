from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .agent import KnowledgeBaseAgent
from .chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from .embeddings import OpenAIEmbedder
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
    print("BENCHMARK: 3 Chunking Strategies vs LocalEmbedder (all-MiniLM-L6-v2)")
    print("=" * 70)
    print(f"\nLoading {len(existing)} documents:")

    docs = []
    for fp in existing:
        doc = load_document(fp)
        if doc:
            docs.append(doc)
            print(f"  [{doc.id}] {len(doc.content)} chars — {doc.metadata}")

    load_dotenv()
    embedder = OpenAIEmbedder()
    print(f"\nEmbedder: {embedder._backend_name}")

    strategies = {
        "FixedSize (500, overlap=100)": FixedSizeChunker(chunk_size=500, overlap=100),
        "Sentence (max 5)": SentenceChunker(max_sentences_per_chunk=5),
        "Recursive (1000) — My": RecursiveChunker(chunk_size=1000),
    }

    queries = [
        {
            "query": "What are the dimensions and pricing of OpenAI text-embedding-3-large per 1K tokens?",
            "gold": "3,072 dimensions, $0.00013 per 1K tokens",
            "filter": None,
        },
        {
            "query": 'What is "Confabulation" according to NIST and how does it pose risks in healthcare?',
            "gold": "Confabulation: GAI generates+confidently presents false content. In healthcare: wrong diagnosis/treatment.",
            "filter": None,
        },
        {
            "query": "What are the main features of the Hugging Face Transformers library?",
            "gold": "Ease of use (2 lines), Flexibility (PyTorch nn.Module), Simplicity (All in one file)",
            "filter": None,
        },
        {
            "query": "Kỹ thuật Chain-of-Thought (CoT) Prompting hoạt động như thế nào và tại sao nó giúp giảm hallucination?",
            "gold": "CoT yêu cầu suy luận từng bước trước khi kết luận, giảm hallucination.",
            "filter": None,
        },
        {
            "query": "Find the AI risk management framework developed by a US government organization. List 5 main risks of Generative AI according to NIST.",
            "gold": "NIST AI 600-1, 5 risks: CBRN, Confabulation, Dangerous Content, Data Privacy, Environmental",
            "filter": {"source": "nist-framework"},
        },
    ]

    for strat_name, chunker in strategies.items():
        print(f"\n{'='*70}")
        print(f"STRATEGY: {strat_name}")
        print(f"{'='*70}")

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

        print(f"Total chunks: {len(chunked_docs)}")

        store = EmbeddingStore(collection_name=f"bench_{strat_name}", embedding_fn=embedder)
        store.add_documents(chunked_docs)

        for i, q in enumerate(queries, 1):
            if q.get("filter"):
                results = store.search_with_filter(q["query"], top_k=3, metadata_filter=q["filter"])
            else:
                results = store.search(q["query"], top_k=3)

            top_doc = results[0]["metadata"].get("doc_id", "?") if results else "none"
            top_score = results[0]["score"] if results else 0
            top_preview = results[0]["content"][:80].replace("\n", " ") if results else ""

            print(f"  Q{i}: doc={top_doc} score={top_score:.4f} | {top_preview}...")


if __name__ == "__main__":
    run_benchmark()
