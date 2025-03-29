from selenium import webdriver
from selenium.webdriver.common.by import By
import logging
import csv
import os


class F2SiteScraper:
    SEASON_IDS = {
        2025: 182,
        2024: 181,
        2023: 180,
        2022: 179,
        2021: 178,
        2020: 177,
        2019: 176,
        2018: 175,
        2017: 174,
    }

    def __init__(self, dirpath="", logger: logging.Logger = None):
        self.dirpath = dirpath
        self.logger = logger if logger else logging.Logger(__name__)

        self.BASE_URL = "https://www.fiaformula2.com"
        self.PATHS = {
            "driver_standings": "Standings/Driver",
            "team_standings": "Standings/Team",
        }

        if self.dirpath and not os.path.exists(self.dirpath):
            self.logger.info(f"Creating directory: {self.dirpath}")
            os.makedirs(self.dirpath)

    def write_data_to_csv(self, headings, content, filename):
        filepath = f"{self.dirpath}/{filename}"
        with open(filepath, mode="w+", newline="") as file:
            writer = csv.writer(file)

            # Write the rows (data)
            writer.writerow(headings)
            writer.writerows(content)

    def get_driver_standings(self, season=2025):
        url = f"{self.BASE_URL}/{self.PATHS['driver_standings']}?seasonId={self.SEASON_IDS[season]}"

        driver = webdriver.Chrome()
        driver.get(url)
        driver.implicitly_wait(1)

        standings_table = driver.find_element(by=By.TAG_NAME, value="table")

        headings_elements = standings_table.find_elements(by=By.TAG_NAME, value="th")

        headings = []

        for heading in headings_elements:
            heading_text = heading.text.split("\n")
            if "SR" in heading_text:
                sr_label = f"{heading_text[0]}-{heading_text[2]}"
                fr_label = f"{heading_text[0]}-{heading_text[3]}"
                headings.append(sr_label)
                headings.append(fr_label)
            else:
                headings.extend(heading_text)

        self.logger.info(headings)
        self.logger.info(len(headings))

        rows_elements = standings_table.find_elements(by=By.TAG_NAME, value="tr")

        content = []

        for row in rows_elements:
            row_data = row.find_elements(by=By.TAG_NAME, value="td")
            row_data_text = []
            for data in row_data:
                row_data_text.extend(data.text.split("\n"))
            row_data_text = row_data_text[1:]
            if len(row_data_text) > 0:
                self.logger.info(row_data_text)
                content.append(row_data_text)

        driver.quit()

        self.write_data_to_csv(headings, content, f"f2_{season}_driver_standings.csv")

    def get_team_standings(self, season=2025):
        url = f"{self.BASE_URL}/{self.PATHS['team_standings']}?seasonId={self.SEASON_IDS[season]}"

        driver = webdriver.Chrome()
        driver.get(url)
        driver.implicitly_wait(1)

        standings_table = driver.find_element(by=By.TAG_NAME, value="table")

        headings_elements = standings_table.find_elements(by=By.TAG_NAME, value="th")

        headings = []

        for heading in headings_elements:
            heading_text = heading.text.split("\n")
            if "SR" in heading_text:
                sr_label = f"{heading_text[0]}-{heading_text[2]}"
                fr_label = f"{heading_text[0]}-{heading_text[3]}"
                headings.append(sr_label)
                headings.append(fr_label)
            else:
                headings.extend(heading_text)

        self.logger.info(headings)
        self.logger.info(len(headings))

        rows_elements = standings_table.find_elements(by=By.TAG_NAME, value="tr")

        content = []

        for row in rows_elements:
            row_data = row.find_elements(by=By.TAG_NAME, value="td")
            row_data_text = []
            for data in row_data:
                row_data_text.extend(data.text.split("\n"))
            row_data_text = row_data_text[1:]
            if len(row_data_text) > 0:
                self.logger.info(row_data_text)
                content.append(row_data_text)

        driver.quit()

        self.write_data_to_csv(headings, content, f"f2_{season}_team_standings.csv")
