import fastf1.core
import fastf1.events
from shiny import App, ui, reactive, render
from shinyswatch import theme
import fastf1
from fastf1.plotting import list_compounds, get_compound_color
from constants import (
    conventional_session_options,
    sprint_session_options,
    year_options,
)
from shinywidgets import output_widget, render_widget
import plotly.express as px


def get_driver_options(session: fastf1.core.Session):
    driver_numbers = session.results
    print(driver_numbers)
    driver_abbreviations = driver_numbers["Abbreviation"].to_list()
    return driver_abbreviations


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("year", label="Year", choices=year_options),
        ui.input_select("event", label="Event", choices={-1: ""}),
        ui.input_select("session", label="Session", choices=[]),
        ui.input_select("driver", label="Driver", choices=[]),
        id="sidebar",
    ),
    ui.navset_tab(
        ui.nav_panel(
            "Laps",
            ui.card(
                ui.output_data_frame("laps_df"),
            ),
        ),
        ui.nav_panel(
            "Telemetry",
            ui.card(ui.input_select("lap", "Lap", choices=[])),
            ui.card(output_widget("lap_speed_plot")),
            ui.card(output_widget("lap_gear_plot")),
            ui.card(output_widget("lap_rpm_plot")),
            ui.card(output_widget("lap_throttle_plot")),
            ui.card(output_widget("lap_brake_plot")),
        ),
        ui.nav_panel(
            "Analysis",
            ui.card(output_widget("tyre_deg_plot")),
            ui.card(output_widget("tyre_stint_boxplot")),
        ),
    ),
    title="F1 Telemetry",
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
                "driver",
                choices=get_driver_options(event_session_data())
                if event_session_data() is not None
                else [],
            )
            if (input.driver() is not None) and (event_session_data() is not None):
                car_data = event_session_data().laps.pick_driver(input.driver())
                lap_numbers = (
                    car_data["LapNumber"].to_list() if car_data is not None else []
                )
                ui.update_select("lap", choices=lap_numbers)

    @reactive.effect
    @reactive.event(input.driver)
    def get_driver_telemetry():
        if input.driver() is not None:
            car_data = event_session_data().laps.pick_driver(input.driver())
            lap_numbers = car_data["LapNumber"].to_list()
            ui.update_select("lap", choices=lap_numbers)

    @render.data_frame
    def laps_df():
        if event_session_data() is not None:
            data = event_session_data().laps.pick_driver(input.driver())
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
    @reactive.event(input.lap)
    def lap_speed_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_driver(input.driver())
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
    @reactive.event(input.lap)
    def lap_gear_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_driver(input.driver())
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
    @reactive.event(input.lap)
    def lap_rpm_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_driver(input.driver())
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
    @reactive.event(input.lap)
    def lap_throttle_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_driver(input.driver())
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
    @reactive.event(input.lap)
    def lap_brake_plot():
        input_lap = int(float(input.lap())) if input.lap() is not None else None
        if input_lap is not None:
            car_data = (
                event_session_data()
                .laps.pick_driver(input.driver())
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
            event_data = event_session_data().laps.pick_drivers(input.driver())
            event_data = event_data[event_data["IsAccurate"]]
            tyre_deg_data = event_data[
                ["LapTime", "TyreLife", "Compound", "Stint"]
            ].sort_values("Stint")
            tyre_deg_data["Stint"] = tyre_deg_data["Stint"].apply(lambda x: int(x))
            tyre_deg_data["LapTime"] = tyre_deg_data["LapTime"].apply(
                lambda x: x.total_seconds()
            )

            compound_colours = list_compounds(event_session_data())
            print(compound_colours)
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
            event_data = event_session_data().laps.pick_drivers(input.driver())
            event_data = event_data[event_data["IsAccurate"]]
            tyre_deg_data = event_data[["LapTime", "TyreLife", "Compound", "Stint"]]
            tyre_deg_data["Stint"] = tyre_deg_data["Stint"].apply(lambda x: int(x))
            tyre_deg_data["LapTime"] = tyre_deg_data["LapTime"].apply(
                lambda x: x.total_seconds()
            )

            compound_colours = list_compounds(event_session_data())
            print(compound_colours)
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


app = App(app_ui, server)
