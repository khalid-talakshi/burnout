import logging

from pyburnout.scrapers import FIASiteScraper

logging.basicConfig(level=logging.INFO)
logger = logging.Logger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

if __name__ == "__main__":
    fia_scraper = FIASiteScraper(logger=logger)
    fia_scraper.bulk_download_all_documents()
