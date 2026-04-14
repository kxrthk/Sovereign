import logging
from PIL import Image
import os
import requests
import json
import base64

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

CHROMA_PATH = r"d:\Sudha - C\Desktop\Sovereign\memories\vision_chroma_db"
OLLAMA_URL = "http://localhost:11434/api/generate"

class VisionAgent:
    """
    The Visual Intelligence (The Eyes) - 100% LOCAL OFFLINE VERSION.
    Uses Ollama (llava) to look at live chart screenshots, and a local ChromaDB 
    RAG system to synthesize advice based on your private trading books.
    """
    def __init__(self, vision_model="llava", text_model="llama3"):
        self.vision_model = vision_model
        self.text_model = text_model
        self.collection = None
        
        logging.info("Initializing Local Vision-RAG Agent...")
        
        if CHROMA_AVAILABLE and os.path.exists(CHROMA_PATH):
            try:
                self.chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
                self.collection = self.chroma_client.get_collection(name="trading_resources")
                logging.info("Local Knowledge Base connected.")
            except Exception as e:
                logging.error(f"Could not connect to local ChromaDB: {e}")
        else:
            logging.warning("ChromaDB not found or not built yet. Run build_vision_kb.py first.")

    def _image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _query_ollama(self, model: str, prompt: str, image_b64: str = None) -> str:
        """Sends a request to local Ollama instance."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        if image_b64:
            payload["images"] = [image_b64]
            
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logging.error(f"Ollama Error: {response.text}")
                return ""
        except requests.exceptions.ConnectionError:
            logging.error("Ollama connection failed. Is Ollama running on localhost:11434?")
            return "ERROR: Ollama offline."
        except Exception as e:
            logging.error(f"Ollama Request Error: {e}")
            return f"ERROR: {str(e)}"

    def analyze_chart(self, image_path: str, context: str = "") -> dict:
        """
        1. V-Model describes the chart.
        2. Description queries RAG.
        3. T-Model reads RAG + Description to give advice.
        """
        logging.info(f"VisionAgent: Scanning chart {image_path} locally...")
        
        # Step 1: Image -> Text (Scanning the chart)
        img_b64 = self._image_to_base64(image_path)
        vision_prompt = "Describe the technical patterns, trend direction, and geometry visible in this trading chart. Keep it technical."
        
        description = self._query_ollama(self.vision_model, vision_prompt, img_b64)
        if "ERROR" in description:
             return {"error": description}
             
        logging.info(f"Local Vision Output: {description[:100]}...")

        # Step 2: Text -> RAG (Searching the libraries)
        knowledge_context = "No specific textbook knowledge found."
        if self.collection:
            try:
                 results = self.collection.query(
                     query_texts=[description],
                     n_results=2
                 )
                 if results and results['documents']:
                     docs = results['documents'][0]
                     knowledge_context = "\\n---\\n".join(docs)
                     logging.info("RAG Match found in local resources.")
            except Exception as e:
                 logging.error(f"RAG Query failed: {e}")

        # Step 3: Synthesis
        synthesis_prompt = f"""
        You are my Trading Buddy. You explain chart setups in simple, direct, jargon-free English.
        
        Context regarding this chart: {context}
        What the visual scanner saw: '{description}'
        What our trading textbooks say about this: '{knowledge_context}'

        Evaluate the setup based strictly on these headers:
        1. Setup Type: Is this a 'Scalp' or 'Swing' play?
        2. The Vibe: What is the current momentum? (Bullish, Bearish, Choppy)
        3. The Numbers:
           - Entry Point: [Extract best guess or tight range]
           - Invalidation (Stop Loss): [Exact price to cut the trade]
           - Profit Target: [Exact price to take profits]
        4. Buddy Advice: One sentence of final advice based on the textbook theory.
        """
        
        # We can use the same vision model (llava) to do text if llama3 isn't installed, 
        # but ideally we use a strong text model. We'll use the vision model to be safe.
        final_advice = self._query_ollama(self.vision_model, synthesis_prompt)
        
        # Step 4: Formatting
        parsed_data = {
            "setup_type": "Data Not Formatted Properly",
            "the_vibe": "",
            "entry": "",
            "stop_loss": "",
            "target": "",
            "buddy_advice": final_advice[:200] + "..." # Raw dump fallback
        }
        
        lines = final_advice.split('\n')
        for line in lines:
             lower_line = line.lower()
             if "setup type:" in lower_line or "1." in lower_line and "setup" in lower_line:
                  parsed_data["setup_type"] = line.split(':', 1)[-1].strip()
             elif "vibe:" in lower_line or "2." in lower_line and "vibe" in lower_line:
                  parsed_data["the_vibe"] = line.split(':', 1)[-1].strip()
             elif "entry point:" in lower_line or "entry:" in lower_line:
                  parsed_data["entry"] = line.split(':', 1)[-1].strip()
             elif "invalidation" in lower_line or "stop loss:" in lower_line:
                  parsed_data["stop_loss"] = line.split(':', 1)[-1].strip()
             elif "profit target:" in lower_line or "target:" in lower_line:
                  parsed_data["target"] = line.split(':', 1)[-1].strip()
             elif "buddy advice:" in lower_line or "4." in lower_line and "advice" in lower_line:
                  parsed_data["buddy_advice"] = line.split(':', 1)[-1].strip()

        return parsed_data

    def render_to_ui_format(self, analysis_result: dict) -> list:
        if "error" in analysis_result:
            return [{"label": "ERROR", "value": analysis_result["error"]}]
            
        return [
            {"label": "Play Style", "value": analysis_result.get("setup_type", "Unknown")},
            {"label": "Current Vibe", "value": analysis_result.get("the_vibe", "Unknown")},
            {"label": "Entry Zone", "value": analysis_result.get("entry", "0.00")},
            {"label": "Hard Stop", "value": analysis_result.get("stop_loss", "0.00")},
            {"label": "Smart Target", "value": analysis_result.get("target", "0.00")},
            {"label": "Final Word", "value": analysis_result.get("buddy_advice", "")},
        ]

if __name__ == "__main__":
    vision = VisionAgent()
    res = vision.analyze_chart("mock_path.png", "TATASTEEL 15-minute timeframe.")
    print("Vision Analysis:")
    for item in vision.render_to_ui_format(res):
        print(f"{item['label']}: {item['value']}")
