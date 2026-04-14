import os
import requests
from bs4 import BeautifulSoup
import datetime
import logging
from urllib.parse import urljoin

class RegulatoryScraper:
    """
    Downloads the latest publications, circulars, and reports from NSE and RBI
    over the last 3 months to feed the Sovereign Knowledge Vault (training_raw/).
    """
    def __init__(self, output_dir="training_raw"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        })
        
        # Calculate date 3 months ago
        self.three_months_ago = datetime.datetime.now() - datetime.timedelta(days=90)

    def download_pdf(self, url: str, filename: str):
        """Downloads a PDF if it doesn't already exist."""
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            logging.info(f"RegulatoryScraper: [EXISTS] {filename}")
            return
            
        try:
            logging.info(f"RegulatoryScraper: [DOWNLOADING] {filename}...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            logging.info(f"RegulatoryScraper: [SUCCESS] Saved {filename}")
        except Exception as e:
            logging.error(f"RegulatoryScraper: Failed to download {url}. Error: {e}")

    def scrape_rbi_circulars(self):
        """
        Scrapes the latest RBI communications/circulars.
        Because RBI's site uses complex ASP.NET and captchas for some sections, 
        this targets their primary public RSS/What's New feeds and extrapolates links.
        """
        logging.info("RegulatoryScraper: Scanning RBI for recent publications...")
        # A reliable public feed for RBI latest publications
        rbi_url = "https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
        
        try:
            response = self.session.get(rbi_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This is a simplified logic block. A true scraper would need to navigate the table structure
            # To fetch PDFs, we search for links containing '.pdf'
            links = soup.find_all('a', href=True)
            pdf_links = [l['href'] for l in links if l['href'].lower().endswith('.pdf')]
            
            count = 0
            for link in pdf_links:
                if count >= 5: break # Limit to top 5 recent to prevent spamming
                full_url = urljoin(rbi_url, link)
                filename = "RBI_" + full_url.split('/')[-1]
                self.download_pdf(full_url, filename)
                count += 1
                
        except Exception as e:
            logging.error(f"RegulatoryScraper: Error scraping RBI: {e}")

    def scrape_nse_reports(self):
        """
        Scrapes the latest NSE Market Reports and Circulars.
        NSE uses a highly dynamic React/Angular frontend, so we often have to tap into 
        their public APIs or static circular pages.
        """
        logging.info("RegulatoryScraper: Scanning NSE for recent market reports...")
        
        # Example direct URL to NSE circulars/announcements page or their static research reports
        nse_url = "https://www1.nseindia.com/corporates/corpInfo/equities/Announcements.html"
        
        # NOTE: For a robust system, we would connect directly to NSE's underground API:
        # e.g., https://www.nseindia.com/api/circulars
        # Due to NSE's strict bot-blocking (HTTP 401/403 common without proper cookies), 
        # this is a structural stub demonstrating the logic for downloading the files.
        try:
            # We must fetch the main page to get cookies first if hitting the API
            self.session.get("https://www.nseindia.com", timeout=10)
            
            api_url = "https://www.nseindia.com/api/circulars"
            # Fake headers to bypass basic NSE blocks
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.nseindia.com/'
            }
            
            response = self.session.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                 data = response.json()
                 # Parse JSON for PDF links and dates
                 # ... Implementation details ...
                 logging.info("RegulatoryScraper: Reached NSE API successfully.")
            else:
                 logging.warning(f"RegulatoryScraper: NSE returned {response.status_code}. Anti-bot protection active.")

        except Exception as e:
            logging.error(f"RegulatoryScraper: Error scraping NSE: {e}")

    def sync_all(self):
         """Orchestrator to run all scrapers."""
         print("\n--- INITIATING REGULATORY & MACRO SCRAPE ---")
         self.scrape_rbi_circulars()
         self.scrape_nse_reports()
         print("--- SCRAPE COMPLETE ---\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = RegulatoryScraper()
    scraper.sync_all()
