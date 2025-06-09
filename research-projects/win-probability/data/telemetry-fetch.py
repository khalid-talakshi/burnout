import fastf1
import pandas as pd

# fastf1.logger.LoggingManager.set_level(logging.ERROR)
circuit = "monza"


def get_driver_lap_data(circuit):
    years = [i for i in range(2018, 2025)]
    results = []

    for year in years:
        print(f"data for year {year}")
        session = fastf1.get_session(year, circuit, "R")
        session.load()

        drivers = session.drivers

        for driver in drivers:
            print(f"analyzing telemetry for {driver} - {year}")

            driver_info = session.get_driver(driver)
            driver_id = driver_info["DriverId"]

            laps = session.laps.pick_drivers(driver)
            for lap in laps["LapNumber"]:
                current_lap = session.laps.pick_drivers(driver).pick_laps(lap)
                try:
                    current_lap_telem = current_lap.get_pos_data().add_driver_ahead()
                except Exception as e:
                    print("telemetry error", e)
                    continue
                position = current_lap["Position"].item()
                distance = list(current_lap_telem["DistanceToDriverAhead"])
                # end_driver = list(current_lap_telem['DriverAhead'])[-1]
                net_distance_gap = distance[-1] - distance[0]
                # print(f'{driver} {circuit}: {lap} - {position} - {net_distance_gap} (driver ahead: {end_driver})')
                results.append(
                    {
                        "year": year,
                        "driver_num": driver,
                        "driver_id": driver_id,
                        "circuit": circuit,
                        "lap": lap,
                        "position": position,
                        "gap_ahead": distance[-1],
                        "net_gain": net_distance_gap,
                    }
                )

    results_df = pd.DataFrame(data=results)
    print(results_df)
    return results_df


df = get_driver_lap_data(circuit)
df.to_csv(f"driver-lap-data-{circuit}.csv", index=False)
