import os
import json
import logging
from google import genai
from typing import Dict, Any

class Librarian:
    """
    Manages the Knowledge Vault. 
    Uploads PDFs to the Gemini Files API and caches them locally to avoid redundant uploads and save money.
    """
    def __init__(self, raw_dir="training_raw", cache_file="library_card.json"):
        self.raw_dir = raw_dir
        self.cache_file = cache_file
        
        # Ensure directory exists
        if not os.path.exists(self.raw_dir):
            os.makedirs(self.raw_dir)
            
        self._load_cache()
        # You need to configure your API key before calling upload
        try:
             self.client = genai.Client()
        except Exception as e:
             logging.warning(f"Librarian: Could not initialize Gemini Client: {e}")
             self.client = None

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            except json.JSONDecodeError:
                self.cache = {}
        else:
            self.cache = {}
            
    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=4)

    def sync_library(self) -> Dict[str, Any]:
        """
        Scans training_raw/. Uploads new PDFs to Gemini API,
        caches their URI in library_card.json, and returns all active file references.
        """
        logging.info("Librarian: Syncing Knowledge Vault...")
        
        # 0. Fetch the latest market research from Regulators (NSE/RBI)
        try:
            from regulatory_scraper import RegulatoryScraper
            scraper = RegulatoryScraper(self.raw_dir)
            scraper.sync_all()
        except ImportError:
            logging.warning("Librarian: regulatory_scraper.py missing. Skipping auto-download.")
        except Exception as e:
            logging.error(f"Librarian: Regulatory Scrape Failed. {e}")

        active_files = {}
        
        for filename in os.listdir(self.raw_dir):
            if filename.endswith(".pdf"):
                file_path = os.path.join(self.raw_dir, filename)
                file_stat = os.stat(file_path)
                
                # Check if it's already cached and unmodified
                if filename in self.cache and self.cache[filename].get("size") == file_stat.st_size:
                    logging.info(f"Librarian: [CACHED] {filename}")
                    active_files[filename] = self.cache[filename]
                    continue
                    
                # Needs Upload
                logging.info(f"Librarian: [UPLOADING] {filename} to Gemini...")
                if not self.client:
                     logging.warning("Librarian: Skipping upload, no GenAI client.")
                     continue
                try:
                    uploaded_file = self.client.files.upload(file=file_path, display_name=filename)
                    
                    file_record = {
                        "name": uploaded_file.name,
                        "uri": uploaded_file.uri,
                        "size": file_stat.st_size
                    }
                    
                    self.cache[filename] = file_record
                    active_files[filename] = file_record
                    self._save_cache()
                    logging.info(f"Librarian: [SUCCESS] {filename} indexed.")
                    
                except Exception as e:
                    logging.error(f"Librarian: Failed to upload {filename}. Error: {e}")
                    
        return active_files

    def get_all_document_names(self):
        """Returns the Gemini representation names of all cached documents for passing to the API."""
        return [record['name'] for record in self.cache.values()]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    lib = Librarian()
    # Note: Requires GENAI_API_KEY to be set
    print("Library Index:", lib.cache)
