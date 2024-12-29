from bs4 import BeautifulSoup
from urllib.parse import quote
import requests
import os


season_paths = {
    "2024": "season-2024-2043",
    "2023": "season-2023-2042"
}

championship_paths = {
    "f1": "fia-formula-one-world-championship-14",
    "f2": "formula-2-championship-44",
    "f3": "fia-formula-3-championship-1012"
}

event_paths = {
    "bahrain-test": "Bahrain Test Season",
    "bahrain": "Bahrain Grand Prix",
    "australia": "Australian Grand Prix"
}

BASE_URL = "https://www.fia.com"
DOCUMENT_PATH = "documents/list"

BASE_DOCS_PATH = "./fia-docs"

current_seasion = '2024'
current_championship = 'f2'
current_event = 'australia'

url = f"{BASE_URL}/{DOCUMENT_PATH}/season/{season_paths.get(current_seasion)}/championships/{championship_paths.get(current_championship)}/event/{quote(event_paths.get(current_event))}"

html_content = requests.get(url).content

soup = BeautifulSoup(html_content, "html.parser")

documents = soup.find_all("div", class_="node-decision-document")

for document in documents:
    inner_element = document.find("a")
    site_link = inner_element.get("href")
    name_element = inner_element.find("div", class_="field-name-title-field").find("div", class_="field-item")
    doc_name = name_element.get_text()

    docs_folder = f"{BASE_DOCS_PATH}/{current_seasion}/{current_championship}/{current_event}" 

    os.makedirs(docs_folder, exist_ok=True)

    with open(f"{docs_folder}/{doc_name}.pdf", "wb") as f:
        doc_res = requests.get(f"{BASE_URL}{site_link}")
        f.write(doc_res.content)