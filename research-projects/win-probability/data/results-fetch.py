import requests
import pandas as pd
import time
import warnings

warnings.filterwarnings("ignore")


BASE_URL = "http://api.jolpi.ca/ergast/f1"
circuit = "monza"
years = [x for x in range(1950, 2026)]

result_data = []

for year in years:
    print(f"fetching {year}")
    results_url = f"{BASE_URL}/{year}/circuits/{circuit}/results"

    data = requests.get(results_url).json()

    race_data = data["MRData"]["RaceTable"]["Races"]

    results = []
    for race in race_data:
        results.append(race["Results"])
    print(results)

    for res in results:
        result_data.extend(
            list(
                map(
                    lambda x: {
                        "number": x["number"],
                        "driver": x["Driver"]["driverId"],
                        "constructor": x["Constructor"]["constructorId"],
                        "position": x["position"],
                        "grid": x["grid"],
                        "year": year,
                    },
                    res,
                )
            )
        )

    time.sleep(4)

result_df = pd.DataFrame(data=result_data)

result_df.to_csv(f"driver-results-{circuit}.csv", index=False)
