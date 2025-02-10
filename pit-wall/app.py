import fastf1
import fastf1.core
import fastf1.events
import plotly.express as px
from constants import (
    conventional_session_options,
    sprint_session_options,
    year_options,
    telemetry_metrics,
    position_metrics,
)
from fastf1.plotting import get_compound_color, get_driver_color, list_compounds
from shiny import App, reactive, render, ui
from shinyswatch import theme
from shinywidgets import output_widget, render_widget
import numpy as np


def get_driver_options(session: fastf1.core.Session):
    driver_numbers = session.results
    driver_abbreviations = driver_numbers["Abbreviation"].to_list()
    return driver_abbreviations


def clean_results_data(session: fastf1.core.Session):
    data = session.results
    data["Q1"] = data["Q1"].apply(lambda x: x.total_seconds())
    data["Q2"] = data["Q2"].apply(lambda x: x.total_seconds())
    data["Q3"] = data["Q3"].apply(lambda x: x.total_seconds())
    data["Time"] = data["Time"].apply(lambda x: x.total_seconds())
    return data

def create_vector_sets(data: fastf1.core.Telemetry):
    data["dx"] = data["X"].diff()
    data["dy"] = data["Y"].diff()
    
    def create_angles(xs, ys):
        angles = [None]
        assert len(xs) == len(ys)
        for i in range(1, len(xs)):
            v1 = np.array([xs.iloc[i-1], ys.iloc[i-1]])
            v2 = np.array([xs.iloc[i], ys.iloc[i]])
            dot = np.dot(v1, v2)
            v1_norm = np.linalg.norm(v1)
            v2_norm = np.linalg.norm(v2)
            angle = np.arccos(dot / (v1_norm * v2_norm))
            angle = np.degrees(angle)
            angles.append(angle)
        return angles
    data["angles"] = create_angles(data["X"], data["Y"])
    data["cumulative_angles"] = data["angles"].cumsum()
    return data


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("year", label="Year", choices=year_options),
        ui.input_select("event", label="Event", choices={-1: ""}),
        ui.input_select("session", label="Session", choices=[]),
        id="sidebar",
    ),
    ui.navset_tab(
        ui.nav_panel(
            "Home",
            ui.card(
                ui.output_ui("session_info"),
            ),
            ui.card(
                ui.output_data_frame("results_df"),
            ),
        ),
        ui.nav_panel(
            "Laps",
            ui.card(
                ui.layout_columns(
                    ui.input_select("laps_driver", label="Driver", choices=[]),
                )
            ),
            ui.card(
                ui.output_data_frame("laps_df"),
            ),
        ),
        ui.nav_panel(
            "Telemetry",
            ui.card(
                ui.layout_columns(
                    ui.input_select("telemetry_driver", label="Driver", choices=[]),
                    ui.input_select("lap", "Lap", choices=[]),
                )
            ),
            ui.card(output_widget("lap_speed_plot")),
            ui.card(output_widget("lap_gear_plot")),
            ui.card(output_widget("lap_rpm_plot")),
            ui.card(output_widget("lap_throttle_plot")),
            ui.card(output_widget("lap_brake_plot")),
        ),
        ui.nav_panel(
            "Analysis",
            ui.card(
                ui.layout_columns(
                    ui.input_select("analysis_driver", label="Driver", choices=[])
                )
            ),
            ui.card(output_widget("tyre_deg_plot")),
            ui.card(output_widget("tyre_stint_boxplot")),
        ),
        ui.nav_panel(
            "Location",
            ui.card(
                ui.card(
                    ui.layout_columns(
                        ui.input_select("location_driver", label="Driver", choices=[]),
                        ui.input_select("location_lap", "Lap", choices=[]),
                        ui.input_select(
                            "metric_select",
                            "Metric",
                            choices=["Speed", "RPM", "Throttle", "Brake", "nGear"],
                        ),
                    )
                ),
                ui.card(output_widget("location_telemetry")),
                ui.card(
                    ui.layout_columns(
                        output_widget("location_xy_2d"),
                        output_widget("location_z_2d"),
                    )
                ),
                ui.card(
                    output_widget("delta_xy_2d"),
                ),
            ),
        ),
        ui.nav_panel(
            "Quali Comp",
            ui.card(
                ui.layout_columns(
                    ui.input_select(
                        "quali_comp_driver_1", label="Driver 1", choices=[]
                    ),
                    ui.input_select(
                        "quali_comp_driver_2", label="Driver 2", choices=[]
                    ),
                )
            ),
        ),
    ),
    title="Pit Wall",
    theme=theme.darkly,
)


def get_session_options(event_type):
    if event_type == "conventional":
        return conventional_session_options
    elif event_type == "sprint_qualifying":
        return sprint_session_options
    return []


def server(input, output, session):
    event_schedule_data = reactive.value(None)
    event_data = reactive.value(None)
    event_session_data = reactive.value(None)

    base_depenedencies = [input.year, input.event, input.session]
    laps_dependencies = [input.laps_driver, *base_depenedencies]

    @reactive.effect
    @reactive.event(input.year)
    def print_year():
        if input.year() != "":
            data = fastf1.get_event_schedule(year=int(input.year()))
            event_schedule_data.set(data)
            round_series = event_schedule_data()["RoundNumber"].to_list()
            event_name_series = event_schedule_data()["EventName"].to_list()

            event_options = {-1: ""}
            for i in range(len(round_series)):
                event_options[round_series[i]] = event_name_series[i]
            ui.update_select("event", choices=event_options)

    @reactive.effect
    @reactive.event(input.event)
    def handle_event_select():
        round_number = int(input.event())
        data = (
            event_schedule_data().get_event_by_round(round_number)
            if (event_schedule_data() is not None) and (round_number > 0)
            else None
        )
        event_data.set(data)
        if event_data() is not None:
            ui.update_select(
                "session",
                choices=get_session_options(event_data()["EventFormat"]),
            )

    @reactive.effect
    @reactive.event(input.session)
    def get_session():
        if input.session() is not None and input.event() is not None:
            data = event_data().get_session(input.session())
            if data is not None:
                data.load(laps=True)
            event_session_data.set(data)

            ui.update_select(
                "laps_driver",
                choices=get_driver_options(event_session_data())
                if event_session_data() is not None
                else [],
            )
            ui.update_select(
                "telemetry_driver",
                choices=get_driver_options(event_session_data())
                if event_session_data() is not None
                else [],
            )
            ui.update_select(
                "analysis_driver",
                choices=get_driver_options(event_session_data())
                if event_session_data() is not None
                else [],
            )
            ui.update_select(
                "location_driver",
                choices=get_driver_options(event_session_data())
                if event_session_data() is not None
                else [],
            )

    @render.ui
    def session_info():
        if event_session_data() is not None:
            session_info_data = event_session_data().session_info
            return ui.TagList(
                ui.markdown(
                    f"""
                # {session_info_data["Meeting"]["Name"]} 
                Session Type: {session_info_data["Type"]}\n
                Start Time: {session_info_data["StartDate"]}
                """
                )
            )
        return ui.markdown("No session data")

    @render.data_frame
    def results_df():
        if event_session_data() is not None:
            data = clean_results_data(event_session_data())
            return render.DataTable(data)
        return

    @reactive.effect
    @reactive.event(*laps_dependencies)
    def get_driver_telemetry():
        if input.laps_driver() is not None:
            car_data = event_session_data().laps.pick_drivers(input.laps_driver())
            lap_numbers = car_data["LapNumber"].to_list()
            ui.update_select("lap", choices=lap_numbers)
            ui.update_select("location_lap", choices=lap_numbers)

    @render.data_frame
    def laps_df():
        print("===", event_session_data())
        if event_session_data() is not None:
            data = event_session_data().laps.pick_drivers(input.laps_driver())
            data["Lap"] = data["LapTime"].apply(lambda x: x.total_seconds())
            data["Lap Number"] = data["LapNumber"]
            data["Sector 1"] = data["Sector1Time"].apply(lambda x: x.total_seconds())
            data["Sector 2"] = data["Sector2Time"].apply(lambda x: x.total_seconds())
            data["Sector 3"] = data["Sector3Time"].apply(lambda x: x.total_seconds())
            data["Valid"] = data["IsAccurate"].apply(lambda x: True if x else False)
            data["Compound"] = data["Compound"]
            data = data[
                [
                    "Driver",
                    "Lap Number",
                    "Lap",
                    "Valid",
                    "Sector 1",
                    "Sector 2",
                    "Sector 3",
                    "Compound",
                ]
            ]
            return render.DataTable(
                data,
                filters=True,
                styles=[
                    {
                        "style": {
                            "backgroundColor": "#2D2D2D",
                            "color": "white",
                        },
                    }
                ],
            )
        return None

    @render_widget
    def lap_speed_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_drivers(input.telemetry_driver())
                .pick_lap(input_lap)
                .get_telemetry()
            )

            speed_data = car_data[["Time", "Speed"]]
            speed_data["Time"] = speed_data["Time"].apply(lambda x: x.total_seconds())

            speed_plot = px.line(
                speed_data,
                x="Time",
                y="Speed",
                template="plotly_dark",
            )
            speed_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )

            return speed_plot
        return None

    @render_widget
    def lap_gear_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_drivers(input.telemetry_driver())
                .pick_lap(input_lap)
                .get_telemetry()
            )

            speed_data = car_data[["Time", "nGear"]]
            speed_data["Time"] = speed_data["Time"].apply(lambda x: x.total_seconds())

            speed_plot = px.line(
                speed_data,
                x="Time",
                y="nGear",
                template="plotly_dark",
            )
            speed_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )

            return speed_plot
        return None

    @render_widget
    def lap_rpm_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_drivers(input.telemetry_driver())
                .pick_lap(input_lap)
                .get_telemetry()
            )

            speed_data = car_data[["Time", "RPM"]]
            speed_data["Time"] = speed_data["Time"].apply(lambda x: x.total_seconds())

            speed_plot = px.line(
                speed_data,
                x="Time",
                y="RPM",
                template="plotly_dark",
            )
            speed_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )

            return speed_plot
        return None

    @render_widget
    def lap_throttle_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_drivers(input.telemetry_driver())
                .pick_lap(input_lap)
                .get_telemetry()
            )

            speed_data = car_data[["Time", "Throttle"]]
            speed_data["Time"] = speed_data["Time"].apply(lambda x: x.total_seconds())

            speed_plot = px.line(
                speed_data,
                x="Time",
                y="Throttle",
                template="plotly_dark",
            )
            speed_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )

            return speed_plot
        return None

    @render_widget
    def lap_brake_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_drivers(input.telemetry_driver())
                .pick_lap(input_lap)
                .get_telemetry()
            )

            speed_data = car_data[["Time", "Brake"]]
            speed_data["Time"] = speed_data["Time"].apply(lambda x: x.total_seconds())

            speed_plot = px.line(
                speed_data,
                x="Time",
                y="Brake",
                template="plotly_dark",
            )
            speed_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )

            return speed_plot
        return None

    @render_widget
    def tyre_deg_plot():
        if event_session_data() is not None:
            event_data = event_session_data().laps.pick_drivers(input.analysis_driver())
            event_data = event_data[event_data["IsAccurate"]]
            tyre_deg_data = event_data[
                ["LapTime", "TyreLife", "Compound", "Stint"]
            ].sort_values("Stint")
            tyre_deg_data["Stint"] = tyre_deg_data["Stint"].apply(lambda x: int(x))
            tyre_deg_data["LapTime"] = tyre_deg_data["LapTime"].apply(
                lambda x: x.total_seconds()
            )

            compound_colours = list_compounds(event_session_data())
            colour_compound_map = {
                compound: get_compound_color(compound, event_session_data())
                for compound in compound_colours
            }

            tyre_deg_plot = px.scatter(
                tyre_deg_data,
                x="TyreLife",
                y="LapTime",
                symbol="Stint",
                color="Compound",
                color_discrete_map=colour_compound_map,
                template="plotly_dark",
            )

            tyre_deg_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )

            tyre_deg_plot.update_layout(
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                )
            )

            return tyre_deg_plot
        return None

    @render_widget()
    def tyre_stint_boxplot():
        if event_session_data() is not None:
            event_data = event_session_data().laps.pick_drivers(input.analysis_driver())
            event_data = event_data[event_data["IsAccurate"]]
            tyre_deg_data = event_data[["LapTime", "TyreLife", "Compound", "Stint"]]
            tyre_deg_data["Stint"] = tyre_deg_data["Stint"].apply(lambda x: int(x))
            tyre_deg_data["LapTime"] = tyre_deg_data["LapTime"].apply(
                lambda x: x.total_seconds()
            )

            compound_colours = list_compounds(event_session_data())
            colour_compound_map = {
                compound: get_compound_color(compound, event_session_data())
                for compound in compound_colours
            }

            tyre_deg_plot = px.box(
                tyre_deg_data,
                x="Stint",
                y="LapTime",
                color="Compound",
                color_discrete_map=colour_compound_map,
                template="plotly_dark",
            )

            tyre_deg_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )

            tyre_deg_plot.update_layout(
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                )
            )

            return tyre_deg_plot
        return None

    @render_widget
    def location_telemetry():
        input_lap = (
            int(float(input.location_lap())) if input.lap() is not None else None
        )
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_drivers(input.location_driver())
                .pick_lap(input_lap)
                .get_telemetry()
            )

            speed_data = car_data[["Time", "X", "Y", "Z"]]
            speed_data["Time"] = speed_data["Time"].apply(lambda x: x.total_seconds())

            driver_colour = get_driver_color(
                input.location_driver(), event_session_data()
            )

            speed_plot = px.scatter_3d(
                speed_data,
                x="X",
                y="Y",
                z="Z",
            )
            speed_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )
            speed_plot.update_traces(marker=dict(color=driver_colour))

            return speed_plot
        return None

    @render_widget
    def location_xy_2d():
        input_lap = (
            int(float(input.location_lap())) if input.lap() is not None else None
        )
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_drivers(input.location_driver())
                .pick_lap(input_lap)
                .get_telemetry()
            )

            speed_data = car_data[
                ["Time", "X", "Y", "Z", "Speed", "RPM", "Throttle", "Brake", "nGear"]
            ]
            speed_data["Time"] = speed_data["Time"].apply(lambda x: x.total_seconds())
            speed_data["nGear"] = speed_data["nGear"].apply(lambda x: str(x))

            speed_plot = px.scatter(
                speed_data,
                x="X",
                y="Y",
                color=input.metric_select(),
            )
            speed_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )

            return speed_plot
        return None

    @render_widget
    def location_z_2d():
        input_lap = (
            int(float(input.location_lap())) if input.lap() is not None else None
        )
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_drivers(input.location_driver())
                .pick_lap(input_lap)
                .get_telemetry()
            )

            speed_data = car_data[
                ["Time", "X", "Y", "Z", "Speed", "RPM", "Throttle", "Brake", "nGear"]
            ]
            speed_data["Time"] = speed_data["Time"].apply(lambda x: x.total_seconds())

            speed_plot = px.scatter(
                speed_data,
                x="Time",
                y="Z",
                color=input.metric_select(),
            )
            speed_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )
            speed_plot.update_xaxes(color="white")
            return speed_plot
        return None

    @render_widget
    def delta_xy_2d():
        input_lap = (
            int(float(input.location_lap())) if input.lap() is not None else None
        )
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_drivers(input.location_driver())
                .pick_lap(input_lap)
                .get_telemetry()
            )

            speed_data = car_data[
                [*position_metrics, *telemetry_metrics]
            ]
            speed_data["Time"] = speed_data["Time"].apply(lambda x: x.total_seconds())
            speed_data = create_vector_sets(speed_data)
            print(speed_data)

            speed_plot = px.scatter(speed_data, x="Time", y="angles")

            speed_plot.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
            )

            return speed_plot
        return None


app = App(app_ui, server)
