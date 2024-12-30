from bs4 import BeautifulSoup
from urllib.parse import quote
import requests
import os
import logging


class FIASiteScraper:
    def __init__(self, logger: logging.Logger = None):
        self.BASE_URL = "https://www.fia.com"
        self.DOCUMENT_PATH = "documents/list"
        self.BASE_DOCS_PATH = "./fia-docs"

        self.SEASON_PATHS = {
            "2024": "season-2024-2043",
            "2023": "season-2023-2042",
            "2022": "season-2022-2005",
            "2021": "season-2021-1108",
            "2020": "season-2020-1059",
            "2019": "season-2019-971",
            "2015": "season-2015-249",
        }

        self.CHAMPIONSHIP_PATHS = {
            "f1": "fia-formula-one-world-championship-14",
            "f2": "formula-2-championship-44",
            "f3": "fia-formula-3-championship-1012",
        }

        self.EVENT_PATHS = {
            "bahrain-test": "Bahrain Tests Season",
            "bahrain": "Bahrain Grand Prix",
            "australia": "Australian Grand Prix",
            "azerbaijan": "Azerbaijan Grand Prix",
            "azerbaidjan": "Azerbaidjan Grand Prix",
            "abh dhabi": "Abu Dhabi Grand Prix",
            "austria": "Austrian Grand Prix",
            "belgian": "Belgian Grand Prix",
            "belgium": "Belgium Grand Prix",
            "british": "British Grand Prix",
            "canada": "Canadian Grand Prix",
            "chinese": "Chinese Grand Prix",
            "dutch": "Dutch Grand Prix",
            "eifel": "Eifel Grand Prix",
            "f1 abu dhabi": "F1 Etihad Airways Abu Dhabi Grand Prix",
            "f1 70th": "Formula 1 70th Anniversary Grand Prix",
            "french": "French Grand Prix",
            "german": "German Grand Prix",
            "imola": "Emilia Romagna Grand Prix",
            "hungary": "Hungarian Grand Prix",
            "italy": "Italian Grand Prix",
            "japan": "Japanese Grand Prix",
            "vegas": "Las Vegas Grand Prix",
            "mexico": "Mexico City Grand Prix",
            "miami": "Miami Grand Prix",
            "monaco": "Monaco Grand Prix",
            "qatar": "Qatar Grand Prix",
            "brazil": "São Paulo Grand Prix",
            "saudi": "Saudi Arabian Grand Prix",
            "singapore": "Singapore Grand Prix",
            "spain": "Spanish Grand Prix",
            "usa": "United States Grand Prix",
        }

        self.logger = logger if logger else logging.Logger(__name__)

    def download_documents(
        self, current_season: str, current_championship: str, current_event: str
    ):
        self.logger.info("Beginning Scraping of Documents")
        self.logger.info(f"Season: {current_season}")
        self.logger.info(f"Championship: {current_championship}")
        self.logger.info(f"Event: {current_event}")
        url = f"{self.BASE_URL}/{self.DOCUMENT_PATH}/season/{self.SEASON_PATHS.get(current_season)}/championships/{self.CHAMPIONSHIP_PATHS.get(current_championship)}/event/{quote(self.EVENT_PATHS.get(current_event))}"
        self.logger.info(f"URL: {url}")

        html_content = requests.get(url).content

        soup = BeautifulSoup(html_content, "html.parser")

        documents = soup.find_all("div", class_="node-decision-document")
        li_flag = False

        if len(documents) == 0:
            documents = soup.find_all("li", class_="document-row")
            li_flag = True
            if len(documents) == 0:
                self.logger.info("No Documents Found")

        for document in documents:
            inner_element = document.find("a")
            if not inner_element:
                continue
            site_link = inner_element.get("href")
            name_element = (
                inner_element.find("div", class_="title")
                if li_flag
                else inner_element.find("div", class_="field-name-title-field").find(
                    "div", class_="field-item"
                )
            )
            doc_name = name_element.get_text().strip()

            docs_folder = f"{self.BASE_DOCS_PATH}/{current_season}/{current_championship}/{current_event}"

            os.makedirs(docs_folder, exist_ok=True)

            self.logger.info(f"Writing File - {doc_name}.pdf")

            file_path = f"{docs_folder}/{doc_name}.pdf"

            if os.path.exists(file_path):
                self.logger.info("File Exists - Skipping")
                continue

            with open(file_path, "wb") as f:
                doc_res = requests.get(f"{self.BASE_URL}{site_link}")
                f.write(doc_res.content)

    def bulk_download_all_documents(self, year="2024"):
        for championship_key in dict.keys(self.CHAMPIONSHIP_PATHS):
            for event_key in dict.keys(self.EVENT_PATHS):
                self.download_documents(year, championship_key, event_key)
