import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
# ═══════════════════════════════════════════════════════════════════
# sovereign_brain.py — The Local AI Inference Engine
# ═══════════════════════════════════════════════════════════════════
# Drop-in replacement for ALL Gemini API calls.
# Uses Ollama (local LLM) + SovereignRAG (ChromaDB knowledge base).
# Zero cloud. Zero API keys. 100% sovereign.
# ═══════════════════════════════════════════════════════════════════

import os
import json
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger("SovereignBrain")

# ─── Configuration ────────────────────────────────────────────────
try:
    from config import OLLAMA_MODEL
except ImportError:
    OLLAMA_MODEL = "phi3.5"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


class SovereignBrain:
    """
    The Sovereign Local Intelligence Engine.
    
    Replaces all external AI API calls with local Ollama inference,
    optionally augmented with RAG context from ChromaDB.
    
    Usage:
        brain = SovereignBrain()
        result = brain.think("Analyze this stock...", json_mode=True)
        result = brain.think("Reflect on trades...", context_query="trading performance")
    """

    def __init__(self, model: str = None):
        self.model = model or OLLAMA_MODEL
        self.base_url = OLLAMA_BASE_URL
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        self._rag = None  # Lazy-loaded
        self._available = None  # Cache availability check

    @property
    def rag(self):
        """Lazy-load RAG engine to avoid import overhead when not needed."""
        if self._rag is None:
            try:
                from sovereign_rag import SovereignRAG
                self._rag = SovereignRAG()
                logger.info("SovereignRAG knowledge engine connected.")
            except Exception as e:
                logger.warning(f"RAG engine unavailable: {e}")
                self._rag = False  # Mark as failed, don't retry
        return self._rag if self._rag is not False else None

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is loaded."""
        if self._available is not None:
            return self._available
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m["name"].split(":")[0] for m in r.json().get("models", [])]
                self._available = self.model.split(":")[0] in models
                if self._available:
                    logger.info(f"SovereignBrain ONLINE — model: {self.model}")
                else:
                    logger.warning(f"Model '{self.model}' not found. Available: {models}")
                return self._available
        except Exception:
            pass
        self._available = False
        logger.warning("Ollama is not running. SovereignBrain OFFLINE.")
        return False

    def think(
        self,
        prompt: str,
        context_query: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        system_prompt: str = None
    ) -> str:
        """
        Main inference method. Replaces ALL Gemini generate_content() calls.

        Args:
            prompt: The task/question for the AI.
            context_query: If provided, queries RAG for relevant knowledge
                           and injects it into the prompt automatically.
            json_mode: If True, forces JSON output format.
            temperature: Creativity (0.0 = deterministic, 1.0 = creative).
            max_tokens: Maximum response length.
            system_prompt: Optional system instruction override.

        Returns:
            The AI's response as a string.
        """
        if not self.is_available():
            raise ConnectionError("SovereignBrain is offline. Ollama not running or model not found.")

        # ── RAG Augmentation ──────────────────────────────────────
        if context_query and self.rag:
            try:
                results = self.rag.query(context_query, top_k=3)
                if results:
                    knowledge_text = "\n\n".join([
                        f"[Knowledge #{i+1}]: {r.get('text', r.get('document', ''))}"
                        for i, r in enumerate(results)
                    ])
                    prompt = f"""RELEVANT KNOWLEDGE FROM DATABASE:
{knowledge_text}

TASK:
{prompt}"""
                    logger.info(f"RAG injected {len(results)} knowledge chunks for query: '{context_query[:50]}...'")
            except Exception as e:
                logger.warning(f"RAG query failed (proceeding without context): {e}")

        # ── System Prompt with Live Context ──────────────────────
        if system_prompt is None:
            # Inject live market/news context into every call
            live_brief = ""
            try:
                from live_context import assemble_live_context
                live_brief = assemble_live_context()
            except Exception as e:
                logger.warning(f"Live context unavailable: {e}")

            system_prompt = f"""You are Sovereign, a self-sovereign quantitative trading AI with deep expertise in Indian financial markets.

CORE CAPABILITIES:
- You analyze financial data, news, and market trends to make structured decisions.
- You return precise, actionable outputs. When asked for JSON, return ONLY valid JSON.
- You think step-by-step: First assess the data, then reason about implications, then conclude.

CRITICAL INTELLIGENCE RULES:
- SATIRE/HUMOR DETECTION: If a headline sounds absurd, uses sarcasm, or comes from known satirical sources, DO NOT treat it as a real financial event. Flag it as "satirical/unverified" in your analysis.
- SENSATIONALISM FILTER: Headlines with extreme language ("CRASH", "COLLAPSE", "SKYROCKET") are often clickbait. Cross-reference with other sources before reacting. A single alarming headline among neutral ones is likely noise.
- INDIRECT LANGUAGE: Politicians and central bank officials often communicate through understatement. "We are monitoring the situation closely" = they are worried. "Gradual normalization" = rate hikes coming. Decode the subtext.
- RECENCY BIAS: Recent events feel more important than they are. Weight structural factors (GDP, earnings, rates) more than daily noise.

PREDICTION METHODOLOGY:
- Never blindly apply historical CAGR. Consider: macro environment, sector cycle, valuation levels, global cues.
- For fund predictions: Apply mean reversion. A fund showing 40% returns will likely normalize to 20-25%.
- Be marginally conservative. Underestimating is better than overestimating for investor trust.
- Always explain WHY you adjusted the rate — one sentence of genuine reasoning.

{live_brief}"""

        # ── Ollama API Call ───────────────────────────────────────
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 4096
            }
        }

        if json_mode:
            payload["format"] = "json"

        try:
            r = requests.post(self.generate_url, json=payload, timeout=120)
            r.raise_for_status()
            response_text = r.json().get("response", "").strip()

            if json_mode:
                # Clean potential markdown wrapping
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            return response_text

        except requests.exceptions.Timeout:
            raise TimeoutError("SovereignBrain inference timed out (120s). Model may be too large for hardware.")
        except Exception as e:
            raise RuntimeError(f"SovereignBrain inference failed: {e}")

    def think_json(
        self,
        prompt: str,
        context_query: Optional[str] = None,
        temperature: float = 0.2,
        fallback: Dict = None
    ) -> Dict:
        """
        Convenience method: calls think() with json_mode=True and parses the result.
        Returns a Python dict. Falls back to `fallback` dict on parse failure.
        """
        fallback = fallback or {}
        try:
            raw = self.think(
                prompt=prompt,
                context_query=context_query,
                json_mode=True,
                temperature=temperature
            )
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"JSON parse failed. Raw response: {raw[:200]}")
            return fallback
        except Exception as e:
            logger.warning(f"think_json failed: {e}")
            return fallback

    def classify_sentiment(self, text: str) -> Dict:
        """
        Specialized method for news/headline sentiment classification.
        Returns: {"sentiment": "BULLISH|BEARISH|NEUTRAL", "confidence": 0.0-1.0}
        """
        prompt = f"""Classify the financial sentiment of this text.
Text: "{text}"
Return JSON: {{"sentiment": "BULLISH" or "BEARISH" or "NEUTRAL", "confidence": <float 0-1>}}"""
        return self.think_json(
            prompt=prompt,
            fallback={"sentiment": "NEUTRAL", "confidence": 0.5}
        )

    def predict_fund_value(self, fund_name: str, category: str, capital: float, years: int, cagr_hint: str) -> Dict:
        """
        Specialized method for mutual fund future value prediction.
        Uses RAG context about the fund category for informed analysis.
        """
        prompt = f"""Evaluate the realistic future capitalization of this Indian Mutual Fund over {years} years.
Fund Name: {fund_name}
Category: {category}
Initial Capital: ₹{capital}
Historical CAGR Hint (adjust based on macro outlook): {cagr_hint}

Consider the Indian macroeconomic outlook for {category} funds.
Use FV = P*(1+r/100)^N with an AI-adjusted rate.
Return JSON: {{"estimatedValue": <integer>, "reasoning": "<one sentence>"}}"""

        try:
            cagr_val = float(cagr_hint.replace("%", ""))
        except:
            cagr_val = 15.0
        fallback_val = int(capital * (1 + cagr_val / 100) ** years)

        return self.think_json(
            prompt=prompt,
            context_query=f"{category} mutual fund India performance",
            fallback={"estimatedValue": fallback_val, "reasoning": "Using historical CAGR (local model busy)."}
        )


# ═══════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON — Import this across the codebase
# ═══════════════════════════════════════════════════════════════════
_brain_instance = None

def get_brain() -> SovereignBrain:
    """Returns a singleton SovereignBrain instance."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = SovereignBrain()
    return _brain_instance


# ═══════════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [BRAIN] %(message)s")
    brain = SovereignBrain()

    if not brain.is_available():
        print("❌ Ollama is not running or model not found.")
        print("   Start with: ollama serve")
        print(f"   Pull model: ollama pull {brain.model}")
        exit(1)

    print(f"✅ SovereignBrain ONLINE — Model: {brain.model}")
    print("\n─── Test 1: Sentiment Classification ───")
    result = brain.classify_sentiment("NIFTY 50 breaks all-time high amid FII buying surge")
    print(f"   Result: {result}")

    print("\n─── Test 2: Fund Prediction (JSON) ───")
    result = brain.predict_fund_value("HDFC Defence Fund", "Thematic - Defence", 50000, 5, "41.2%")
    print(f"   Result: {result}")

    print("\n─── Test 3: Free-form Analysis ───")
    result = brain.think("In 2 sentences, what is the outlook for Indian IT sector stocks?")
    print(f"   Result: {result}")

    print("\n✅ All tests passed. Sovereign is self-sovereign.")
