"""
rag_ingest.py — Sovereign Knowledge Ingestion Pipeline
========================================================
Batch ingests all Sovereign data sources into ChromaDB:

  1. Research PDFs from Resources/ (5 categories, 42 PDFs)
  2. RBI regulatory PDFs from training_raw/ (5 PDFs)
  3. Trading memories from memories/ (decision_log, reflections)
  4. Market intelligence from memories/latest_news_raw.json

Usage:
    python rag_ingest.py                  # Full ingestion
    python rag_ingest.py --pdfs-only      # Only PDFs
    python rag_ingest.py --memory-only    # Only memories + intel

Supports incremental ingestion — already-ingested files are skipped via content hashing.
"""

import os
import sys
import json
import time
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger("RAG_Ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [INGEST] %(message)s")

# Paths
RESOURCES_DIR    = "./Resources"
TRAINING_RAW_DIR = "./training_raw"
MEMORIES_DIR     = "./memories"
DECISION_LOG     = "./memories/decision_log.json"
REFLECTIONS_DIR  = "./memories/reflections"
NEWS_RAW         = "./memories/latest_news_raw.json"
INGEST_MANIFEST  = "./vector_db/ingest_manifest.json"


def _load_manifest() -> dict:
    """Load the ingestion manifest (tracks which files have been ingested)."""
    if os.path.exists(INGEST_MANIFEST):
        try:
            with open(INGEST_MANIFEST, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_manifest(manifest: dict):
    """Save the ingestion manifest."""
    os.makedirs(os.path.dirname(INGEST_MANIFEST), exist_ok=True)
    with open(INGEST_MANIFEST, 'w') as f:
        json.dump(manifest, f, indent=2)


def _file_hash(filepath: str) -> str:
    """Quick hash of file size + mtime for change detection."""
    stat = os.stat(filepath)
    return hashlib.md5(f"{filepath}:{stat.st_size}:{stat.st_mtime}".encode()).hexdigest()


def _extract_pdf_text(filepath: str) -> list:
    """
    Extract text from a PDF, returning a list of {page, text} dicts.
    Uses PyPDF2 for reliable extraction.
    """
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        logger.error("PyPDF2 not installed. Run: pip install PyPDF2")
        return []

    pages = []
    try:
        reader = PdfReader(filepath)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"page": i + 1, "text": text.strip()})
    except Exception as e:
        logger.error(f"Failed to extract text from {filepath}: {e}")

    return pages


def _detect_category(filepath: str) -> str:
    """Detect the category from the folder name."""
    parts = Path(filepath).parts
    for part in parts:
        if part in [
            "Algorithmic_Trading_and_Systems",
            "Crypto_and_Blockchain",
            "Machine_Learning_and_AI",
            "Market_Theory_and_Analysis",
            "Quantitative_Strategies_and_Risk"
        ]:
            return part.replace("_", " ").title()
    if "training_raw" in str(filepath).lower():
        return "Regulatory (RBI)"
    return "General"


# ══════════════════════════════════════════════════════════════════
# INGESTION FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def ingest_pdfs(rag, manifest: dict) -> int:
    """Ingest all PDFs from Resources/ and training_raw/."""
    total_chunks = 0
    pdf_dirs = []

    # Collect all PDF directories
    if os.path.isdir(RESOURCES_DIR):
        for subdir in os.listdir(RESOURCES_DIR):
            full_path = os.path.join(RESOURCES_DIR, subdir)
            if os.path.isdir(full_path):
                pdf_dirs.append(full_path)

    if os.path.isdir(TRAINING_RAW_DIR):
        pdf_dirs.append(TRAINING_RAW_DIR)

    for pdf_dir in pdf_dirs:
        for filename in os.listdir(pdf_dir):
            if not filename.lower().endswith('.pdf'):
                continue

            filepath = os.path.join(pdf_dir, filename)
            file_key = filepath.replace("\\", "/")
            current_hash = _file_hash(filepath)

            # Skip if already ingested and unchanged
            if manifest.get(file_key) == current_hash:
                logger.info(f"[SKIP] {filename} (already ingested)")
                continue

            logger.info(f"[PROCESSING] {filename}...")
            start = time.time()

            pages = _extract_pdf_text(filepath)
            if not pages:
                logger.warning(f"[EMPTY] {filename} — no extractable text")
                continue

            category = _detect_category(filepath)

            # Ingest each page as a separate text block
            file_chunks = 0
            for page_data in pages:
                metadata = {
                    "source": filename,
                    "category": category,
                    "page": page_data["page"],
                    "type": "research_paper",
                    "filepath": file_key
                }
                chunks_added = rag.ingest_text(
                    page_data["text"],
                    metadata=metadata,
                    collection="research_papers"
                )
                file_chunks += chunks_added

            elapsed = time.time() - start
            total_chunks += file_chunks
            manifest[file_key] = current_hash
            logger.info(f"[DONE] {filename} → {file_chunks} chunks in {elapsed:.1f}s")

    return total_chunks


def ingest_decision_log(rag, manifest: dict) -> int:
    """Ingest trading decision history."""
    if not os.path.exists(DECISION_LOG):
        logger.info("[SKIP] No decision_log.json found")
        return 0

    current_hash = _file_hash(DECISION_LOG)
    if manifest.get("decision_log") == current_hash:
        logger.info("[SKIP] decision_log.json (unchanged)")
        return 0

    try:
        with open(DECISION_LOG, 'r') as f:
            decisions = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read decision log: {e}")
        return 0

    total_chunks = 0
    # Group decisions into batches of 10 for coherent chunks
    batch_size = 10
    for i in range(0, len(decisions), batch_size):
        batch = decisions[i:i + batch_size]
        text = "Trade Decisions:\n"
        for d in batch:
            text += (f"- {d.get('timestamp', 'N/A')}: {d.get('symbol', '?')} "
                     f"→ {d.get('signal', '?')} (conf: {d.get('confidence', 0):.2f}) "
                     f"| {d.get('reason', 'N/A')}\n")

        metadata = {
            "source": "decision_log",
            "type": "trade_decision",
            "batch_start": i,
            "batch_end": min(i + batch_size, len(decisions))
        }
        total_chunks += rag.ingest_memory(text, metadata=metadata)

    manifest["decision_log"] = current_hash
    logger.info(f"[DONE] decision_log → {total_chunks} chunks from {len(decisions)} decisions")
    return total_chunks


def ingest_reflections(rag, manifest: dict) -> int:
    """Ingest self-reflection reports."""
    if not os.path.isdir(REFLECTIONS_DIR):
        logger.info("[SKIP] No reflections directory found")
        return 0

    total_chunks = 0
    for filename in os.listdir(REFLECTIONS_DIR):
        if not filename.endswith('.txt'):
            continue

        filepath = os.path.join(REFLECTIONS_DIR, filename)
        file_key = f"reflection:{filename}"
        current_hash = _file_hash(filepath)

        if manifest.get(file_key) == current_hash:
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        except IOError:
            continue

        if not text.strip():
            continue

        metadata = {
            "source": filename,
            "type": "self_reflection",
            "date": filename.replace(".txt", "")
        }
        chunks = rag.ingest_memory(text, metadata=metadata)
        total_chunks += chunks
        manifest[file_key] = current_hash

    logger.info(f"[DONE] Reflections → {total_chunks} chunks")
    return total_chunks


def ingest_news_intelligence(rag, manifest: dict) -> int:
    """Ingest latest news data."""
    if not os.path.exists(NEWS_RAW):
        logger.info("[SKIP] No latest_news_raw.json found")
        return 0

    current_hash = _file_hash(NEWS_RAW)
    if manifest.get("news_raw") == current_hash:
        logger.info("[SKIP] latest_news_raw.json (unchanged)")
        return 0

    try:
        with open(NEWS_RAW, 'r', encoding='utf-8') as f:
            news_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read news data: {e}")
        return 0

    total_chunks = 0

    # Handle both list and dict formats
    articles = news_data if isinstance(news_data, list) else news_data.get("articles", [])

    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", article.get("description", ""))
        source = article.get("source", "unknown")

        if not title and not summary:
            continue

        text = f"Headline: {title}\n{summary}" if summary else f"Headline: {title}"
        metadata = {
            "source": f"news:{source}",
            "type": "news_article",
            "title": title[:200]
        }
        total_chunks += rag.ingest_intelligence(text, metadata=metadata)

    manifest["news_raw"] = current_hash
    logger.info(f"[DONE] News intelligence → {total_chunks} chunks from {len(articles)} articles")
    return total_chunks


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def run_full_ingestion():
    """Execute the complete ingestion pipeline."""
    from sovereign_rag import SovereignRAG

    logger.info("=" * 60)
    logger.info("SOVEREIGN RAG INGESTION PIPELINE")
    logger.info("=" * 60)

    start_time = time.time()
    rag = SovereignRAG()

    if not rag.is_ready:
        logger.error("RAG engine not ready. Aborting.")
        return

    manifest = _load_manifest()

    pdfs_only = "--pdfs-only" in sys.argv
    memory_only = "--memory-only" in sys.argv

    total = 0

    if not memory_only:
        logger.info("\n── Phase 1: Research PDFs ──")
        total += ingest_pdfs(rag, manifest)

    if not pdfs_only:
        logger.info("\n── Phase 2: Decision Log ──")
        total += ingest_decision_log(rag, manifest)

        logger.info("\n── Phase 3: Reflections ──")
        total += ingest_reflections(rag, manifest)

        logger.info("\n── Phase 4: News Intelligence ──")
        total += ingest_news_intelligence(rag, manifest)

    _save_manifest(manifest)

    elapsed = time.time() - start_time
    stats = rag.get_stats()

    logger.info("\n" + "=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info(f"  Total new chunks ingested: {total}")
    logger.info(f"  Time elapsed: {elapsed:.1f}s")
    logger.info(f"  Collection sizes:")
    for name, count in stats["collections"].items():
        logger.info(f"    {name}: {count} chunks")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_full_ingestion()
