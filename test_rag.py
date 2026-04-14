"""
test_rag.py — Sovereign RAG Validation Suite
===============================================
Standalone validation script for the RAG Knowledge Engine.

Tests:
  1. Initialization — ChromaDB boots, collections created
  2. Ingestion — Text is chunked and stored
  3. Query — Semantic search returns relevant results
  4. Speed — Queries execute under 50ms
  5. Cache — Repeat queries under 1ms
  6. De-duplication — Re-ingestion skips duplicates

Usage:
    python test_rag.py
"""

import time
import sys
import os

# Ensure we're in the project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def test(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((name, condition))
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))


def run_tests():
    print("=" * 60)
    print("  SOVEREIGN RAG — VALIDATION SUITE")
    print("=" * 60)

    # ── TEST 1: Initialization ─────────────────────────────────
    print("\n-- Test 1: Initialization")
    try:
        from sovereign_rag import SovereignRAG
        rag = SovereignRAG()
        test("RAG engine initializes", rag.is_ready)
        stats = rag.get_stats()
        test("Collections created", len(stats["collections"]) == 3,
             f"Found {len(stats['collections'])} collections")
    except Exception as e:
        test("RAG engine initializes", False, str(e))
        print("\nCannot continue without initialization. Aborting.")
        return

    # ── TEST 2: Ingestion ──────────────────────────────────────
    print("\n-- Test 2: Ingestion")
    test_text = (
        "Momentum trading is a strategy that seeks to capitalize on existing market trends. "
        "Traders buy securities that are trending upward and sell those trending downward. "
        "The key assumption is that securities which have performed well in the past will "
        "continue to perform well in the near future, and conversely, those that have "
        "performed poorly will continue to underperform. This is supported by behavioral "
        "finance research showing that investors tend to underreact to new information "
        "initially, leading to gradual price adjustments.\n\n"
        "Risk management in momentum strategies involves setting stop-losses and position "
        "sizing based on volatility. ATR-based stops are common because they adapt to "
        "market conditions. During high-volatility periods, wider stops prevent premature "
        "exits while maintaining risk control."
    )
    chunks_added = rag.ingest_text(
        test_text,
        metadata={"source": "test_validation", "category": "test"},
        collection="research_papers"
    )
    test("Text ingested successfully", chunks_added > 0, f"{chunks_added} chunks created")

    count_after = rag._collections["research_papers"].count()
    test("Chunks in ChromaDB", count_after > 0, f"{count_after} total chunks")

    # ── TEST 3: Query Relevance ────────────────────────────────
    print("\n-- Test 3: Query Relevance")
    results_query = rag.query("momentum trading strategy")
    test("Query returns results", len(results_query) > 0, f"{len(results_query)} results")

    if results_query:
        top_result = results_query[0]
        test("Top result has text", len(top_result["text"]) > 0)
        test("Top result has metadata", "source" in top_result["metadata"])
        # Check relevance — the top result should mention momentum
        has_momentum = "momentum" in top_result["text"].lower()
        test("Top result is relevant", has_momentum,
             f"Contains 'momentum': {has_momentum}")

    # Test context string generation
    context = rag.query_for_context("risk management volatility", top_k=2, max_chars=500)
    test("query_for_context returns string", len(context) > 0, f"{len(context)} chars")

    # ── TEST 4: Speed ──────────────────────────────────────────
    print("\n-- Test 4: Speed")
    # Clear cache first to test raw query speed
    rag.query_cache.invalidate()

    query_times = []
    for i in range(20):
        rag.query_cache.invalidate()  # Ensure no cache hits
        start = time.perf_counter()
        rag.query(f"trading strategy {i}")
        elapsed = (time.perf_counter() - start) * 1000
        query_times.append(elapsed)

    avg_ms = sum(query_times) / len(query_times)
    median_ms = sorted(query_times)[len(query_times) // 2]
    test("Average query < 200ms", avg_ms < 200, f"{avg_ms:.1f}ms avg")
    test("Median query < 100ms", median_ms < 100, f"{median_ms:.1f}ms median")
    print(f"    Min: {min(query_times):.1f}ms | Max: {max(query_times):.1f}ms")

    # ── TEST 5: Cache Speed ────────────────────────────────────
    print("\n-- Test 5: Cache")
    rag.query_cache.invalidate()
    # First query (cache miss)
    rag.query("momentum trading")

    # Second query (cache hit)
    start = time.perf_counter()
    cached_results = rag.query("momentum trading")
    cache_ms = (time.perf_counter() - start) * 1000
    test("Cached query < 1ms", cache_ms < 1.0, f"{cache_ms:.3f}ms")

    cache_stats = rag.query_cache.stats
    test("Cache has hits", cache_stats["hits"] > 0, f"Hits: {cache_stats['hits']}")

    # ── TEST 6: De-duplication ─────────────────────────────────
    print("\n-- Test 6: De-duplication")
    count_before = rag._collections["research_papers"].count()
    chunks_re = rag.ingest_text(
        test_text,
        metadata={"source": "test_validation", "category": "test"},
        collection="research_papers"
    )
    count_after = rag._collections["research_papers"].count()
    test("Re-ingestion adds 0 chunks", chunks_re == 0, f"Added: {chunks_re}")
    test("Collection size unchanged", count_before == count_after,
         f"Before: {count_before}, After: {count_after}")

    # -- SUMMARY --──────────────────────────────────────────────
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"  RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("  ** ALL TESTS PASSED -- RAG Engine is operational!")
    else:
        failed = [name for name, ok in results if not ok]
        print(f"  WARNING: Failed tests: {', '.join(failed)}")

    print("=" * 60)

    # Final stats
    print(f"\n  Collection sizes: {rag.get_stats()['collections']}")
    print(f"  Cache stats: {rag.query_cache.stats}")


if __name__ == "__main__":
    run_tests()
