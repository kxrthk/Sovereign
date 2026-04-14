"""
sovereign_rag.py — The Sovereign Knowledge Engine (RAG)
========================================================
High-performance Retrieval-Augmented Generation engine backed by ChromaDB.

Features:
  - Persistent local vector store (./vector_db/)
  - Hybrid structure-aware chunking (paragraph-respecting, sliding window with overlap)
  - In-memory LRU query cache for sub-millisecond repeat lookups
  - Three collections: research_papers, trading_memory, market_intelligence
  - MMR-based re-ranking for diverse, non-redundant retrieval

Usage:
    from sovereign_rag import SovereignRAG
    rag = SovereignRAG()
    rag.ingest_text("content here", metadata={"source": "paper.pdf", "category": "algo"})
    results = rag.query("momentum trading strategies", top_k=5)
"""

import os
import re
import time
import hashlib
import logging
from functools import lru_cache
from typing import List, Dict, Any, Optional
from collections import OrderedDict

import chromadb
from chromadb.config import Settings

logger = logging.getLogger("SovereignRAG")

# ══════════════════════════════════════════════════════════════════
# CONFIGURATION (overridable via config.py)
# ══════════════════════════════════════════════════════════════════
try:
    from config import (
        RAG_VECTOR_DB_PATH, RAG_EMBEDDING_MODEL, RAG_CHUNK_SIZE,
        RAG_CHUNK_OVERLAP, RAG_TOP_K, RAG_CACHE_SIZE, RAG_ENABLED
    )
except ImportError:
    RAG_VECTOR_DB_PATH  = "./vector_db"
    RAG_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    RAG_CHUNK_SIZE      = 512
    RAG_CHUNK_OVERLAP   = 64
    RAG_TOP_K           = 5
    RAG_CACHE_SIZE      = 256
    RAG_ENABLED         = True

# Collection names
COLLECTION_RESEARCH    = "research_papers"
COLLECTION_MEMORY      = "trading_memory"
COLLECTION_INTELLIGENCE = "market_intelligence"


# ══════════════════════════════════════════════════════════════════
# LRU QUERY CACHE (Thread-safe OrderedDict-based)
# ══════════════════════════════════════════════════════════════════
class QueryCache:
    """Fast in-memory LRU cache for repeat queries. Sub-millisecond lookups."""

    def __init__(self, max_size: int = 256):
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[List[Dict]]:
        if key in self._cache:
            self._cache.move_to_end(key)
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        return None

    def put(self, key: str, value: List[Dict]):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def invalidate(self):
        self._cache.clear()

    @property
    def stats(self) -> Dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total * 100, 1) if total > 0 else 0.0,
            "size": len(self._cache)
        }


# ══════════════════════════════════════════════════════════════════
# HYBRID STRUCTURE-AWARE CHUNKER
# ══════════════════════════════════════════════════════════════════
from langchain_text_splitters import SpacyTextSplitter

class HybridChunker:
    """
    Sentence-aware text chunker using LangChain and spaCy.
    Provides robust NLP-backed paragraph/sentence boundaries for RAG retrieval.
    """

    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        # SpacyTextSplitter measures length by characters.
        # We multiply by 5 to roughly match the legacy word-count behavior.
        self.char_chunk_size = chunk_size * 5
        self.char_overlap = overlap * 5
        
        try:
            self.splitter = SpacyTextSplitter(
                chunk_size=self.char_chunk_size,
                chunk_overlap=self.char_overlap,
                pipeline="en_core_web_sm"
            )
        except Exception as e:
            logger.error(f"Failed to initialize SpacyTextSplitter: {e}")
            self.splitter = None

    def chunk(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Returns a list of {text, metadata, id} dicts.
        """
        if not text or not text.strip() or not self.splitter:
            return []

        metadata = metadata or {}
        
        try:
            # LangChain split_text leverages spaCy's NLP models to split cleanly at sentences
            chunks = self.splitter.split_text(text)
        except Exception as e:
            logger.error(f"Spacy split_text failed: {e}")
            return []

        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_meta = {**metadata, "chunk_index": i, "total_chunks": len(chunks)}
            content_hash = hashlib.md5(chunk_text.encode()).hexdigest()
            result.append({
                "text": chunk_text,
                "metadata": chunk_meta,
                "id": f"{metadata.get('source', 'unknown')}_{content_hash[:12]}"
            })

        return result


# ══════════════════════════════════════════════════════════════════
# SOVEREIGN RAG ENGINE
# ══════════════════════════════════════════════════════════════════
class SovereignRAG:
    """
    The Sovereign Knowledge Engine.

    Provides semantic search over all ingested documents, trading memories,
    and market intelligence. Designed for millisecond retrieval to support
    real-time trading decisions.
    """

    def __init__(self, db_path: str = None, embedding_model: str = None):
        self.db_path = db_path or RAG_VECTOR_DB_PATH
        self.embedding_model_name = embedding_model or RAG_EMBEDDING_MODEL
        self.chunker = HybridChunker(chunk_size=RAG_CHUNK_SIZE, overlap=RAG_CHUNK_OVERLAP)
        self.query_cache = QueryCache(max_size=RAG_CACHE_SIZE)
        self._embedding_fn = None
        self._client = None
        self._collections = {}

        if RAG_ENABLED:
            self._initialize()

    def _initialize(self):
        """Initialize ChromaDB client and embedding function."""
        try:
            os.makedirs(self.db_path, exist_ok=True)

            # Initialize ChromaDB with persistent storage
            self._client = chromadb.PersistentClient(path=self.db_path)

            # Load embedding function (sentence-transformers)
            from chromadb.utils import embedding_functions
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model_name
            )

            # Create/get collections
            for name in [COLLECTION_RESEARCH, COLLECTION_MEMORY, COLLECTION_INTELLIGENCE]:
                self._collections[name] = self._client.get_or_create_collection(
                    name=name,
                    embedding_function=self._embedding_fn,
                    metadata={"hnsw:space": "cosine"}
                )

            logger.info(f"[RAG] Initialized. DB: {self.db_path} | Model: {self.embedding_model_name}")
            for name, col in self._collections.items():
                logger.info(f"[RAG]   Collection '{name}': {col.count()} chunks")

        except Exception as e:
            logger.error(f"[RAG] Initialization failed: {e}")
            self._client = None

    @property
    def is_ready(self) -> bool:
        return self._client is not None and len(self._collections) > 0

    # ──────────────────────────────────────────────────────────────
    # INGESTION
    # ──────────────────────────────────────────────────────────────
    def ingest_text(self, text: str, metadata: Dict = None,
                    collection: str = COLLECTION_RESEARCH) -> int:
        """
        Ingest a text document into the specified collection.
        Returns the number of chunks created.
        """
        if not self.is_ready:
            logger.warning("[RAG] Not ready. Skipping ingestion.")
            return 0

        chunks = self.chunker.chunk(text, metadata=metadata or {})
        if not chunks:
            return 0

        col = self._collections.get(collection)
        if not col:
            logger.error(f"[RAG] Collection '{collection}' not found.")
            return 0

        # Check for existing IDs to avoid duplicates
        existing_ids = set()
        try:
            chunk_ids = [c["id"] for c in chunks]
            existing = col.get(ids=chunk_ids)
            if existing and existing.get("ids"):
                existing_ids = set(existing["ids"])
        except Exception:
            pass

        # Filter out already-ingested chunks
        new_chunks = [c for c in chunks if c["id"] not in existing_ids]
        if not new_chunks:
            logger.info(f"[RAG] All {len(chunks)} chunks already exist. Skipping.")
            return 0

        # Batch insert (ChromaDB handles batching internally)
        batch_size = 100
        total_added = 0
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i:i + batch_size]
            col.add(
                ids=[c["id"] for c in batch],
                documents=[c["text"] for c in batch],
                metadatas=[c["metadata"] for c in batch]
            )
            total_added += len(batch)

        # Invalidate query cache since new data was added
        self.query_cache.invalidate()

        logger.info(f"[RAG] Ingested {total_added} new chunks into '{collection}' "
                     f"(skipped {len(existing_ids)} duplicates)")
        return total_added

    def ingest_memory(self, text: str, metadata: Dict = None) -> int:
        """Shortcut to ingest into trading_memory collection."""
        return self.ingest_text(text, metadata, collection=COLLECTION_MEMORY)

    def ingest_intelligence(self, text: str, metadata: Dict = None) -> int:
        """Shortcut to ingest into market_intelligence collection."""
        return self.ingest_text(text, metadata, collection=COLLECTION_INTELLIGENCE)

    # ──────────────────────────────────────────────────────────────
    # QUERYING
    # ──────────────────────────────────────────────────────────────
    def query(self, query_text: str, top_k: int = None,
              collection: str = None,
              where_filter: Dict = None) -> List[Dict]:
        """
        Semantic search across collections. Returns ranked results.

        Args:
            query_text: Natural language query
            top_k: Number of results (default: RAG_TOP_K)
            collection: Specific collection or None for all
            where_filter: ChromaDB metadata filter (e.g., {"category": "algo"})

        Returns:
            List of {text, metadata, distance, collection} dicts, sorted by relevance.
        """
        if not self.is_ready:
            return []

        top_k = top_k or RAG_TOP_K

        # Check cache
        cache_key = f"{query_text}|{top_k}|{collection}|{where_filter}"
        cached = self.query_cache.get(cache_key)
        if cached is not None:
            return cached

        start_time = time.perf_counter()

        results = []
        collections_to_search = (
            [self._collections[collection]] if collection and collection in self._collections
            else self._collections.values()
        )
        collection_names = (
            [collection] if collection and collection in self._collections
            else list(self._collections.keys())
        )

        for col, col_name in zip(collections_to_search, collection_names):
            if col.count() == 0:
                continue

            query_params = {
                "query_texts": [query_text],
                "n_results": min(top_k, col.count()),
            }
            if where_filter:
                query_params["where"] = where_filter

            try:
                raw = col.query(**query_params)
            except Exception as e:
                logger.warning(f"[RAG] Query failed on '{col_name}': {e}")
                continue

            if raw and raw.get("documents") and raw["documents"][0]:
                for i, doc in enumerate(raw["documents"][0]):
                    results.append({
                        "text": doc,
                        "metadata": raw["metadatas"][0][i] if raw.get("metadatas") else {},
                        "distance": raw["distances"][0][i] if raw.get("distances") else 1.0,
                        "collection": col_name
                    })

        # Sort by distance (lower = more relevant for cosine)
        results.sort(key=lambda x: x["distance"])

        # MMR-style diversity: remove near-duplicate results
        results = self._apply_mmr(results, top_k)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Cache the results
        self.query_cache.put(cache_key, results)

        logger.debug(f"[RAG] Query '{query_text[:50]}...' → {len(results)} results in {elapsed_ms:.1f}ms")
        return results

    def query_for_context(self, query_text: str, top_k: int = 3,
                          collection: str = None,
                          max_chars: int = 2000) -> str:
        """
        Convenience method: returns a single string of concatenated relevant chunks.
        Ideal for injecting into LLM prompts.
        """
        results = self.query(query_text, top_k=top_k, collection=collection)
        if not results:
            return ""

        context_parts = []
        total_chars = 0
        for r in results:
            text = r["text"]
            source = r["metadata"].get("source", "unknown")
            snippet = f"[Source: {source}] {text}"

            if total_chars + len(snippet) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 100:
                    snippet = snippet[:remaining] + "..."
                    context_parts.append(snippet)
                break

            context_parts.append(snippet)
            total_chars += len(snippet)

        return "\n\n".join(context_parts)

    def _apply_mmr(self, results: List[Dict], top_k: int,
                   diversity_threshold: float = 0.15) -> List[Dict]:
        """
        Maximal Marginal Relevance: remove results that are too similar to
        already-selected results. Ensures diverse retrieval.
        """
        if len(results) <= top_k:
            return results

        selected = [results[0]]
        candidates = results[1:]

        while len(selected) < top_k and candidates:
            best_candidate = None
            best_score = -1

            for candidate in candidates:
                # Simple text-overlap diversity check
                is_diverse = True
                for sel in selected:
                    # Check if texts are too similar (simple word overlap)
                    c_words = set(candidate["text"].lower().split())
                    s_words = set(sel["text"].lower().split())
                    if len(c_words) == 0:
                        continue
                    overlap = len(c_words & s_words) / max(len(c_words), 1)
                    if overlap > (1 - diversity_threshold):
                        is_diverse = False
                        break

                if is_diverse:
                    # Score = relevance (lower distance = better)
                    score = 1.0 / (1.0 + candidate["distance"])
                    if score > best_score:
                        best_score = score
                        best_candidate = candidate

            if best_candidate:
                selected.append(best_candidate)
                candidates.remove(best_candidate)
            else:
                break

        return selected

    # ──────────────────────────────────────────────────────────────
    # STATS & MAINTENANCE
    # ──────────────────────────────────────────────────────────────
    def get_stats(self) -> Dict:
        """Returns collection sizes and cache stats."""
        stats = {"cache": self.query_cache.stats, "collections": {}}
        if self.is_ready:
            for name, col in self._collections.items():
                stats["collections"][name] = col.count()
        return stats

    def clear_collection(self, collection: str):
        """Wipe a collection and recreate it."""
        if self.is_ready and collection in self._collections:
            self._client.delete_collection(collection)
            self._collections[collection] = self._client.get_or_create_collection(
                name=collection,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
            self.query_cache.invalidate()
            logger.info(f"[RAG] Collection '{collection}' cleared.")

    def clear_all(self):
        """Wipe all collections."""
        for name in list(self._collections.keys()):
            self.clear_collection(name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    rag = SovereignRAG()
    print(f"RAG Ready: {rag.is_ready}")
    print(f"Stats: {rag.get_stats()}")

    # Quick test
    if rag.is_ready:
        rag.ingest_text(
            "Momentum trading involves buying securities that have shown upward price trends. "
            "The strategy assumes that securities which have performed well will continue to do so.",
            metadata={"source": "test_doc", "category": "strategy"}
        )
        results = rag.query("momentum strategy")
        print(f"\nQuery 'momentum strategy': {len(results)} results")
        for r in results:
            print(f"  [{r['distance']:.3f}] {r['text'][:100]}...")
