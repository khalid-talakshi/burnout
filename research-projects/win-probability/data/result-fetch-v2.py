import fastf1
import pandas as pd

circuit = "Bahrain Grand Prix"
shortname = None


def get_circuit_results(circuit):
    global shortname
    years = [x for x in range(1951, 2026)]
    result_data = []

    for year in years:
        event = fastf1.get_event(year, circuit, exact_match=True)

        if event is not None:
            if shortname is None:
                shortname = event["Country"].lower()
            print(f"fetching results for {year}")
            session = event.get_race()
            session.load()

            drivers = session.drivers

            for driver in drivers:
                driver_res = session.get_driver(driver)

                entry = {
                    "number": driver_res["DriverNumber"],
                    "driver": driver_res["DriverId"],
                    "constructor": driver_res["TeamId"],
                    "position": driver_res["Position"],
                    "grid": driver_res["GridPosition"],
                    "year": year,
                }

                result_data.append(entry)

    return pd.DataFrame(result_data)


circuit_results = get_circuit_results(circuit)

print(circuit_results)
circuit_results.to_csv(f"driver-results-{shortname}.csv", index=False)
