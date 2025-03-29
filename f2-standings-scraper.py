from pyburnout.scrapers import F2SiteScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.Logger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logger.addHandler(console_handler)

f2_scrapper = F2SiteScraper(dirpath="./f2-data", logger=logger)

f2_scrapper.get_driver_standings(2025)
f2_scrapper.get_team_standings(2025)
f2_scrapper.get_driver_standings(2024)
f2_scrapper.get_team_standings(2024)
