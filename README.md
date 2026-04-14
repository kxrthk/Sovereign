# Sovereign: The Autonomous Edge AI Financial Core

Welcome to **Sovereign**, a self-evolving quantitative intelligence engine built entirely offline for sovereign environments. 

Sovereign is a powerful AI financial assistant that seamlessly fuses high-speed execution, deep fundamental knowledge extraction (via RAG), real-time global intelligence processing, and self-reflecting cognitive components into a unified, privacy-first interface. At its core, Sovereign operates with **Zero Cloud Dependencies**, using a fully decentralized architecture to orchestrate small local LMs (like Phi-3.5) with unprecedented situational awareness.

---

## ⚡ Core Philosophy

The vision of Sovereign is simple: **True Intelligence requires complete privacy and sovereignty.** API-dependent AI architectures leak trade secrets, suffer from rate-limits, and have opaque data practices. Sovereign executes its reasoning, RAG context handling, strategy alignment, and trading entirely on your local metal.

## 🛠 Features

- **100% Local Inference Engine (`sovereign_brain.py`)** 
  - Drives all analytical systems completely offline using Ollama and high-efficiency models like Microsoft's *Phi-3.5*.
  - Completely drops API keys without losing analytical capacity.
  
- **Contextual Injection & Continuous Awareness (`live_context.py`)**
  - Synthesizes market structures (trending, choppy, crash).
  - Merges real-time parsed sector outputs into a compact brief appended to every local LLM invocation, giving the AI the contextual equivalent of "situational awareness."
  
- **Self-Expanding RAG Knowledge Vault (`sovereign_rag.py`)**
  - Integrated ChromaDB for vectorized local storage.
  - Automatically structures and parses thousands of PDFs, strategy manuals, historic trading logs, and financial news bytes dynamically mapping them for retrieval on relevant queries.
  
- **Automated Data Harvesting (`data_harvester.py`)**
  - Headless infrastructure to capture rolling multi-year AMFI Mutual Fund NAVs and NIFTY index pricing seamlessly with zero user intervention.

- **Dynamic Watchlist Curating & Self-Reflection (`watchlist_curator.py`, `self_reflect.py`)**
  - AI runs nightly self-reflection cycles on end-of-day ledgers, evolving to become sharper at filtering false positives and maintaining emotional regulation.
  - Generates self-epiphanies that are persistent across instances. 
  
- **Sensationalism & Satire Filters (`news_agent.py`)**
  - Evaluates live financial RSS feeds, filtering out satirical noise (meme news) and downgrading clickbait sensationalism in actual fundamental analysis. 

## 🚀 Setup & Execution

Everything is bundled into a one-step automated initialization logic natively for Windows.

1. Ensure **Ollama** is installed and running on your device (must pull a model like `phi3.5`).
2. Clone this repo:
   ```bash
   git clone https://github.com/kxrthk/Sovereign.git
   ```
3. Run the fast-loader script!
   ```cmd
   START_SOVEREIGN_NATIVE.bat
   ```

*The bootscript will natively sequence parallel execution layers: waking Ollama, spooling the RAG embeddings, launching the backend ASGI stack, and hooking into the React Electron dashboard in real-time.*

## 🔒 Security & Safe Modes

Sovereign features a multi-tiered architecture with hard-fails:
- Built-in **DEFCON scaling** (SAFE / CAUTION / DANGER).
- Aggressive API sandboxing — all primary reasoning logic utilizes Local models. Cloud-services run purely as "frozen backups" accessible only using explicit `.env` overriding (`AI_MODE="CLOUD"`).

## 💡 About
Built by [kxrthk](https://github.com/kxrthk). Driven by local intelligence, optimized for quantitative mastery.
