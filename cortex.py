import json
import logging
import os
import time
from news_agent import NewsAgent
from market_regime import MarketRegime
from smart_money_tracker import SmartMoneyTracker

class Cortex:
    """
    The Synthesis Engine (The Cortex).
    Wakes up, reads raw intel gathered by the News Agent, and synthesizes it into `world_view.json`.
    Dictates the DEFCON level (SAFE, CAUTION, or DANGER) to physical override `auto_trader.py`.
    Now augmented with RAG knowledge retrieval for evidence-backed macro analysis.
    """
    def __init__(self, output_file="world_view.json"):
        self.output_file = output_file
        self.agent = NewsAgent()
        self.regime_monitor = MarketRegime()
        self.money_tracker = SmartMoneyTracker()

        # Initialize RAG for research-augmented macro analysis
        self._rag = None
        try:
            from config import RAG_ENABLED
            if RAG_ENABLED:
                from sovereign_rag import SovereignRAG
                self._rag = SovereignRAG()
                if self._rag.is_ready:
                    logging.info("Cortex: RAG Knowledge Engine linked.")
                else:
                    self._rag = None
        except ImportError:
            pass

    def evaluate_world_state(self):
        """
        Polls the news agent, runs the fact checker on extremes,
        and generates a definitive DEFCON level for the trading engine.
        """
        logging.info("Cortex: Waking up to evaluate Global Macro State...")
        
        headlines = self.agent.fetch_latest_headlines()
        red_flags = self.agent.check_for_extreme_news(headlines)
        
        try:
            from config import SOVEREIGN_SIX
            sentiment_scores = self.agent.analyze_sentiment(headlines, SOVEREIGN_SIX)
        except ImportError:
            sentiment_scores = {}
            logging.warning("Cortex: Could not load SOVEREIGN_SIX from config.")

        # FIX: Fetch institutional data via SmartMoneyTracker (was previously undefined)
        try:
            institutional_data = self.money_tracker.analyze_bias()
        except Exception as e:
            logging.warning(f"Cortex: Could not fetch institutional flows: {e}")
            institutional_data = {}
        
        defcon_level = "SAFE"
        justification = "Macro environment is stable. Standard rules apply."
        
        if red_flags:
            logging.warning(f"Cortex: {len(red_flags)} extreme headlines detected. Escalating to CAUTION.")
            defcon_level = "CAUTION"
            justification = "Elevated risk language detected in recent news cycle. Awaiting DDG verification."
            
            # Verify the most serious flags
            verified_threats = 0
            for flag in red_flags:
                 if self.agent.fact_check_ddg(flag):
                      verified_threats += 1
                      
            if verified_threats >= 2: # Requires multiple confirmed threats to shut down the bot
                 logging.critical("Cortex: MULTIPLE VERIFIED MACRO THREATS. Escalating to DANGER.")
                 defcon_level = "DANGER"
                 justification = "Verified extreme news events in progress. Capital preservation mode activated."
            elif verified_threats == 1:
                 defcon_level = "CAUTION"
                 justification = "Single verified extreme news event. Reduce position sizing."
            else:
                 defcon_level = "SAFE"
                 justification = "Extreme news identified as unverified rumor/clickbait. Reverting to SAFE."
                 
        # HARD OVERRIDE: Technical Volatility (The VIX Proxy)
        try:
             regime = self.regime_monitor.get_regime()
             if regime == "CRASH":
                 logging.critical("Cortex: HARD TECHNICAL OVERRIDE. Extreme market volatility detected. Escalating to DANGER.")
                 defcon_level = "DANGER"
                 justification = "Extreme technical volatility detected (Standard Deviation > 2). Hardware halting enabled."
             elif regime == "CHOPPY" and defcon_level == "SAFE":
                 defcon_level = "CAUTION"
                 justification = "Choppy market mechanics overriding SAFE macro environment."
        except Exception as e:
             logging.error(f"Cortex: Failed to query technical regime: {e}")
                 
        # ── RAG RESEARCH AUGMENTATION ─────────────────────────────────
        research_context = ""
        if self._rag:
            try:
                query = f"macro analysis {defcon_level} {justification[:100]}"
                research_context = self._rag.query_for_context(
                    query, top_k=2, collection="research_papers", max_chars=500
                )
                if research_context:
                    justification += f" | Research insight: {research_context[:200]}"
                    logging.info("Cortex: RAG research context enriched justification.")
            except Exception as e:
                logging.debug(f"Cortex: RAG lookup failed: {e}")

        # Synthesize state
        world_view = {
            "defcon": defcon_level,
            "justification": justification,
            "sentiment": sentiment_scores,
            "institutional_flows": institutional_data,
            "timestamp": time.time(),
            "top_themes": [h['title'] for h in headlines[:3]],
            "research_context": research_context[:300] if research_context else ""
        }
        
        self.write_world_view(world_view)
        self._log_defcon_history(defcon_level, justification)
        logging.info(f"Cortex: Evaluation Complete. State locked at {defcon_level}.")
        return defcon_level

    def write_world_view(self, data: dict):
        with open(self.output_file, 'w') as f:
            json.dump(data, f, indent=4)
            
    def get_current_defcon(self) -> str:
        """
        Used by the auto_trader to check the current constraint.
        """
        if not os.path.exists(self.output_file):
            return "SAFE" # Default assumption
            
        try:
            with open(self.output_file, 'r') as f:
                view = json.load(f)
                return view.get("defcon", "SAFE")
        except json.JSONDecodeError:
            return "SAFE"

    def _log_defcon_history(self, defcon_level: str, justification: str):
        """Appends a timestamped DEFCON event to memories/defcon_history.json (rolling 30 entries)."""
        history_path = "memories/defcon_history.json"
        try:
            os.makedirs("memories", exist_ok=True)
            history = []
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    history = json.load(f)
            history.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "defcon": defcon_level,
                "justification": justification
            })
            # Keep only the latest 30 entries
            history = history[-30:]
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            logging.warning(f"Cortex: Failed to write DEFCON history: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cortex = Cortex()
    state = cortex.evaluate_world_state()
    print(f"Final DEFCON State: {state}")
