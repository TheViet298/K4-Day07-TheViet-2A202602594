"""
Benchmark Script for Lab 07 (K4-L3B: Shopee E-Commerce Policies).
Compares retrieval strategies across the 7 Shopee policy documents.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Ensure UTF-8 output in Windows PowerShell
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.agent import KnowledgeBaseAgent
from src.chunking import (
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
    compute_similarity,
)
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore

DATA_DIR = Path(__file__).parent / "data" / "shopee"


class HeadingChunker:
    """Chunk Markdown text by headings (#, ##, ###), keeping header context in subchunks."""

    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self.recursive_fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        sections = re.split(r"(?m)(?=^#{1,3}\s+)", text.strip())
        chunks: list[str] = []
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            if len(sec) <= self.max_chunk_size:
                chunks.append(sec)
            else:
                lines = sec.split("\n", 1)
                header = lines[0] if lines else ""
                body = lines[1] if len(lines) > 1 else ""
                sub_chunks = self.recursive_fallback.chunk(body)
                for sub in sub_chunks:
                    chunks.append(f"{header}\n{sub}".strip())
        return chunks


def load_shopee_corpus() -> list[tuple[dict[str, str], str]]:
    """Reads all .md files in data/shopee/, separating YAML frontmatter from body content."""
    documents = []
    for file_path in sorted(DATA_DIR.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                raw_fm, body = parts[1], parts[2].strip()
                fm = dict(re.findall(r"^(\w+):\s*[\"']?([^\"'\n\r]+)[\"']?", raw_fm, re.M))
                documents.append((fm, body))
                continue
        documents.append(({"doc_id": file_path.stem}, text))
    return documents


BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho đơn hàng thực phẩm tươi sống là bao lâu?",
        "gold_answer": "Trong vòng 24 giờ kể từ lúc đơn hàng được cập nhật trạng thái Giao hàng thành công.",
        "gold_doc": "shopee-returns-policy-for-buyer",
        "filter": None,
        "target_phrase": "24 giờ",
    },
    {
        "id": 2,
        "query": "Đơn hàng có giá trị trên bao nhiêu tiền thì KHÔNG được áp dụng chương trình Đồng kiểm?",
        "gold_answer": "Đơn hàng có giá trị lớn hơn 3.000.000 VND (3 Triệu Đồng).",
        "gold_doc": "shopee-chinh-sach-dong-kiem",
        "filter": None,
        "target_phrase": "3.000.000",
    },
    {
        "id": 3,
        "query": "Người bán bị phạt bao nhiêu điểm Sao Quả Tạ nếu có tỷ lệ giao hàng trễ (LSR) từ 10% trở lên và trên 30 đơn?",
        "gold_answer": "2 điểm phạt Sao Quả Tạ.",
        "gold_doc": "shopee-he-thong-sao-qua-ta",
        "filter": None,
        "target_phrase": "2 điểm",
    },
    {
        "id": 4,
        "query": "Shop đăng bán sản phẩm hàng giả/hàng nhái trên Shopee sẽ phải chịu những chế tài xử lý nào?",
        "gold_answer": "Sản phẩm bị khóa/xóa, cộng điểm phạt Sao Quả Tạ, tạm thời đóng băng hoặc khóa vĩnh viễn tài khoản nếu tái phạm.",
        "gold_doc": "shopee-chinh-sach-hang-cam-va-hang-gia",
        "filter": None,
        "target_phrase": "khóa/xóa",
    },
    {
        "id": 5,
        "query": "Thời hạn khiếu nại quyết định Trả hàng/Hoàn tiền là bao nhiêu ngày?",
        "gold_answer": "Người mua có 15 ngày kể từ ngày giao hàng; Người bán có 2 ngày kể từ khi nhận được thông báo để khiếu nại.",
        "gold_doc": "shopee-returns-policy-for-buyer",
        "filter": {"audience": "buyer"},
        "target_phrase": "15 ngày",
    },
]


def run_benchmark(strategy_name: str, chunker) -> str:
    output_lines = []
    output_lines.append(f"==================================================")
    output_lines.append(f"BENCHMARK RUN: Strategy = {strategy_name}")
    output_lines.append(f"==================================================")

    raw_docs = load_shopee_corpus()
    store = EmbeddingStore(collection_name=f"shopee_{strategy_name}", embedding_fn=_mock_embed)

    total_chunks = 0
    for fm, content in raw_docs:
        chunks = chunker.chunk(content)
        doc_id = fm.get("doc_id", "doc")
        docs_to_add = [
            Document(id=f"{doc_id}#{i}", content=chunk_text, metadata={**fm, "doc_id": doc_id})
            for i, chunk_text in enumerate(chunks)
        ]
        store.add_documents(docs_to_add)
        total_chunks += len(docs_to_add)

    output_lines.append(f"Loaded {len(raw_docs)} files -> Total chunks indexed: {total_chunks}")
    agent = KnowledgeBaseAgent(store=store, llm_fn=lambda prompt: "Trích xuất thành công từ tài liệu.")

    correct_count = 0
    for q in BENCHMARK_QUERIES:
        query_text = q["query"]
        metadata_filter = q["filter"]
        results = store.search_with_filter(query_text, top_k=3, metadata_filter=metadata_filter)

        output_lines.append(f"\n--- Query {q['id']}: {query_text} ---")
        if metadata_filter:
            output_lines.append(f"  [Filter]: {metadata_filter}")
        output_lines.append(f"  Gold Answer: {q['gold_answer']}")

        is_relevant = False
        for rank, res in enumerate(results, 1):
            doc = res["metadata"].get("doc_id")
            text_preview = res["content"][:80].replace("\n", " ")
            has_phrase = q["target_phrase"].lower() in res["content"].lower()
            if has_phrase or doc == q["gold_doc"]:
                is_relevant = True
            output_lines.append(f"  Top-{rank} (Score: {res['score']:.4f}, Doc: {doc}): {text_preview}...")

        if is_relevant:
            correct_count += 1
            output_lines.append(f"  -> Evaluation: PASS (Found relevant context in Top-3)")
        else:
            output_lines.append(f"  -> Evaluation: MISS")

    output_lines.append(f"\nSummary for {strategy_name}: {correct_count}/{len(BENCHMARK_QUERIES)} relevant in Top-3\n")
    return "\n".join(output_lines)


if __name__ == "__main__":
    strategies = {
        "FixedSizeChunker": FixedSizeChunker(chunk_size=300, overlap=30),
        "SentenceChunker": SentenceChunker(max_sentences_per_chunk=2),
        "RecursiveChunker": RecursiveChunker(chunk_size=350),
        "HeadingChunker": HeadingChunker(max_chunk_size=400),
    }

    full_report = []
    for name, chunker in strategies.items():
        res = run_benchmark(name, chunker)
        full_report.append(res)

    Path("ket_qua_benchmark.txt").write_text("\n".join(full_report), encoding="utf-8")
    print("Saved all benchmark comparisons successfully to ket_qua_benchmark.txt")
