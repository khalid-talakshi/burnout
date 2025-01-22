import fastf1.events
from shiny import App, ui, reactive, render
from shinyswatch import theme
import fastf1
from constants import (
    conventional_session_options,
    sprint_session_options,
    year_options,
)
from shinywidgets import output_widget, render_widget
import plotly.express as px


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
            ui.output_data_frame("laps_df"),
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
                choices=event_session_data().drivers
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
            return render.DataTable(
                event_session_data().laps.pick_driver(input.driver())
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


app = App(app_ui, server)
