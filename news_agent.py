import sovereign_encoding  # noqa: F401 — Windows UTF-8 bootstrap (must be first)
import logging
import feedparser
import re
import random
import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

try:
    from config import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = "gemini-2.5-flash"

class NewsAgent:
    """
    The Global Macro Brain.
    Scrapes high-speed RSS feeds (concurrently) and fact-checks extreme news headlines.
    Includes sentiment result caching to prevent redundant Gemini API calls.
    """
    def __init__(self, feeds: List[str] = None):
        self.feeds = feeds or [
            "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms", # ET Markets
            "https://oilprice.com/rss/main", # Global Energy / Oil
            "https://www.tradewindsnews.com/rss", # Shipping / Maritime
            "https://www.mining.com/feed/", # Global Commodities
            "https://techcrunch.com/category/artificial-intelligence/feed/" # Artificial Intelligence
        ]
        self._sentiment_cache = {}   # {fingerprint: scores} — avoids re-calling Gemini for same headlines
        
        # Load the Constitution
        try:
            with open("news_rules.txt", "r") as f:
                self.rules = f.read()
        except FileNotFoundError:
            self.rules = "Default strict interpretation."
            logging.warning("NewsAgent: news_rules.txt missing. Running blind.")

    def _fetch_single_feed(self, url: str) -> List[Dict]:
        """Fetches headlines from a single RSS feed. Called concurrently."""
        results = []
        try:
            import requests
            # Use requests with a strict 5-second timeout to prevent deadlocks
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:5]:
                results.append({
                    "source":    feed.feed.title if hasattr(feed.feed, 'title') else url,
                    "title":     entry.title,
                    "link":      entry.link,
                    "published": entry.published if hasattr(entry, 'published') else "Unknown"
                })
        except Exception as e:
            logging.error(f"NewsAgent: Failed to parse feed {url}: {e}")
        return results

    def fetch_latest_headlines(self) -> List[Dict]:
        """
        Scrapes configured RSS feeds for the latest headlines.
        Uses ThreadPoolExecutor to fetch all feeds concurrently for speed.
        """
        headlines = []
        logging.info(f"NewsAgent: Scanning {len(self.feeds)} feeds concurrently...")

        with ThreadPoolExecutor(max_workers=len(self.feeds)) as executor:
            futures = {executor.submit(self._fetch_single_feed, url): url for url in self.feeds}
            for future in as_completed(futures):
                try:
                    headlines.extend(future.result())
                except Exception as e:
                    logging.error(f"NewsAgent: Feed worker failed: {e}")

        logging.info(f"NewsAgent: Fetched {len(headlines)} headlines total.")
        return headlines

    def check_for_extreme_news(self, headlines: List[Dict]) -> List[str]:
        """
        The Fact-Checker. Looks for specific 'danger' keywords (War, Crash, CEO Arrested, Default).
        Returns a list of dangerous headlines that require the Cortex to raise the DEFCON level.
        """
        danger_keywords = ["war", "crash", "plunge", "arrested", "default", "scam", "halted", "resigns", "emergency"]
        red_flags = []
        
        for article in headlines:
             title_lower = article['title'].lower()
             if any(re.search(r'\b' + word + r'\b', title_lower) for word in danger_keywords):
                  red_flags.append(article['title'])
                  logging.warning(f"NewsAgent: ⚠️ RED FLAG DETECTED - Fact check required: {article['title']}")
                  
        return red_flags
        
    def analyze_sentiment(self, headlines: List[Dict], watchlist: List[str]) -> Dict:
        """
        Uses Gemini to analyze headlines and generate a sentiment score (-1.0 to 1.0)
        for each ticker in the watchlist, as well as a general 'sector_bias'.
        Results are cached by headline fingerprint to avoid duplicate Gemini API calls.
        """
        logging.info("NewsAgent: Running AI Sentiment Analysis on daily news flow...")
        
        default_scores = {ticker: 0.0 for ticker in watchlist}
        default_scores["sector_bias"] = {}
        
        # Cache check — fingerprint the top-20 headlines
        headline_texts = [h['title'] for h in headlines[:20]]
        fingerprint = hashlib.md5(json.dumps(headline_texts, sort_keys=True).encode()).hexdigest()
        if fingerprint in self._sentiment_cache:
            logging.info("NewsAgent: Returning cached sentiment result (headlines unchanged).")
            return self._sentiment_cache[fingerprint]

        # ── LOCAL BRAIN (Primary) ──────────────────────────────────
        try:
            from sovereign_brain import SovereignBrain
            brain = SovereignBrain()
            if brain.is_available():
                prompt = f"""You are a ruthless, quantitative hedge fund algorithm.
Analyze the following recent news headlines:
{headline_texts}

For the following specific Indian market tickers, assess the immediate sentiment impact from -1.0 (extreme bearish) to 1.0 (extreme bullish). 0.0 is neutral.
Tickers: {watchlist}

Also, identify if any specific sectors (e.g., POWER, METALS, FMCG, DEFENCE) have a strong bias.
If any headline appears satirical or clickbait, flag it and do NOT factor it into scores.

Output STRICTLY valid JSON ONLY in this format:
{{
    "TICKER1": 0.5,
    "TICKER2": -0.2,
    "sector_bias": {{"POWER": 0.8, "FMCG": -0.3}}
}}"""
                scores = brain.think_json(prompt=prompt, fallback=default_scores)

                for ticker in watchlist:
                    if ticker not in scores:
                        scores[ticker] = 0.0

                self._sentiment_cache[fingerprint] = scores
                if len(self._sentiment_cache) > 10:
                    oldest_key = next(iter(self._sentiment_cache))
                    del self._sentiment_cache[oldest_key]

                logging.info("NewsAgent: Sentiment Analysis Complete (LOCAL).")
                return scores
        except Exception as e:
            logging.warning(f"NewsAgent: Local brain sentiment failed: {e}")

        # ── CLOUD BACKUP (Gemini) — preserved ────────────────────
        try:
            from config import AI_MODE
        except ImportError:
            AI_MODE = "LOCAL"
        if AI_MODE == "CLOUD":
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    prompt = f"Analyze sentiment for {watchlist} given headlines: {headline_texts}. Return JSON."
                    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
                    result_text = response.text.replace("```json", "").replace("```", "").strip()
                    scores = json.loads(result_text)
                    return scores
                except Exception as e:
                    logging.error(f"NewsAgent: Gemini sentiment failed: {e}")
        return default_scores

    def fact_check_ddg(self, query: str) -> bool:
        """
        Runs a live DuckDuckGo verification search to see if multiple sources report the same event.
        Returns True if verified, False if rumor.
        """
        logging.info(f"NewsAgent: Running DDG verification on '{query}'...")
        try:
            from ddgs import DDGS
            with DDGS() as ddgs_client:
                # Search for the query and grab the top 5 text results
                results = list(ddgs_client.text(query, max_results=5))
                
                if not results:
                     logging.warning("NewsAgent: Verification Result - UNVERIFIED RUMOR (No results).")
                     return False
                     
                # simple verification logic: if multiple distinct sources reported it recently
                sources = set()
                for r in results:
                     # try to extract domain
                     import urllib.parse
                     try:
                         domain = urllib.parse.urlparse(r['href']).netloc
                         sources.add(domain)
                     except:
                         pass
                         
                # If we have at least 2 distinct reputable sources, we consider it confirmed
                is_real = len(sources) >= 2
                
                status = 'CONFIRMED' if is_real else 'UNVERIFIED RUMOR (Single Source)'
                logging.info(f"NewsAgent: Verification Result - {status} ({len(sources)} sources found).")
                return is_real
                
        except Exception as e:
            logging.error(f"NewsAgent: DDG Search failed. Error: {e}")
            return False

    def deep_dive_article(self, url: str) -> str:
        """
        Bypasses RSS extraction to fetch the raw HTML of a single article url.
        Then extracts the text line by line and feeds that massive block to Gemini 
        for a high-confidence ruling on whether the article text matches the headline,
        and if it's a verifiable DANGER or clickbait.
        """
        logging.info(f"NewsAgent (Deep Dive): Initiating full article extraction for {url}")
        try:
            # 1. Fetch HTML
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 2. Extract paragraphs
            paragraphs = soup.find_all('p')
            article_text = "\n".join([p.text.strip() for p in paragraphs if len(p.text.strip()) > 30])

            if len(article_text) < 200:
                logging.warning("NewsAgent (Deep Dive): Could not extract sufficient text. Paywall likely.")
                return "UNVERIFIED"

            prompt = f"""You are Sovereign's Forensic Fact-Checker.
Read the following raw article text to verify a stock market event.
Financial media often uses clickbait headlines that contradict the article body.

ARTICLE TEXT:
{article_text[:4000]}

Determine the TRUE nature based ONLY on the body text.
Reply with strictly ONE of these four exact phrases and nothing else:
VERIFIED_DANGER
VERIFIED_BULLISH
CLICKBAIT
UNVERIFIED"""

            # 3. Use local brain
            try:
                from sovereign_brain import SovereignBrain
                brain = SovereignBrain()
                if brain.is_available():
                    result = brain.think(prompt=prompt, temperature=0.1, max_tokens=32).strip().upper()
                    if result in ["VERIFIED_DANGER", "VERIFIED_BULLISH", "CLICKBAIT", "UNVERIFIED"]:
                        logging.info(f"NewsAgent (Deep Dive LOCAL): Verdict -> {result}")
                        return result
            except Exception as e:
                logging.warning(f"NewsAgent: Local deep dive failed: {e}")

            # Cloud backup
            try:
                from config import AI_MODE
            except ImportError:
                AI_MODE = "LOCAL"
            if AI_MODE == "CLOUD":
                api_key = os.environ.get("GEMINI_API_KEY")
                if api_key:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    gemini_response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
                    result = gemini_response.text.strip().upper()
                    if result in ["VERIFIED_DANGER", "VERIFIED_BULLISH", "CLICKBAIT", "UNVERIFIED"]:
                        return result

            return "UNVERIFIED"

        except Exception as e:
            logging.error(f"NewsAgent (Deep Dive): Extraction failed: {e}")
            return "UNVERIFIED"

if __name__ == "__main__":
    agent = NewsAgent()
    latest = agent.fetch_latest_headlines()
    print(f"Parsed {len(latest)} headlines.")
    
    # Inject a fake dangerous headline to test fact checking
    latest.append({"title": "Major Telecom CEO Arrested in Scam", "source": "FakeNews"})
    
    red_flags = agent.check_for_extreme_news(latest)
    for flag in red_flags:
        agent.fact_check_ddg(flag)
