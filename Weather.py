import os
from datetime import datetime
import datetime
import psycopg2
import pandas as pd
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

USER = os.environ.get('DB_USER')
PASS = os.environ.get('DB_PASS')
HOST = os.environ.get('DB_HOST')
PORT = os.environ.get('DB_PORT')

GRAPH_INTERVAL = os.environ.get("GRAPH_INTERVAL", 1000*10)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

app.title = 'Denton Weather'


app_color = {"graph_bg": "#082255", "graph_line": "#007ACE"}

app.layout = html.Div(
    [
        # header
        html.Div(
            [
                html.Div(
                    [
                        html.H4("Weather Streaming", className="app__header__title"),
                        html.P(
                            "This app continually queries a SQL database and displays live charts of weather data",
                            className="app__header__title--grey",
                        ),
                    ],
                    className="app__header__desc",
                ),
            ],
            className="app__header",
        ),
        html.Div(
            [
                # Weather graph
                html.Div(
                    [
                        html.Div(
                            [html.H6("Temperature (Degree F)", className="graph__title")]
                        ),
                        dcc.Graph(
                            id="temp-graph",
                            figure=dict(
                                layout=dict(
                                    plot_bgcolor=app_color["graph_bg"],
                                    paper_bgcolor=app_color["graph_bg"],
                                )
                            ),
                        ),
                        dcc.Interval(
                            id="interval-component",
                            interval=int(GRAPH_INTERVAL),
                            n_intervals=0,
                        ),
                    ],
                    className="two-thirds column temp__container",
                ),
                # html.Div(
                #     [
                #         # histogram
                #         html.Div(
                #             [
                #                 html.Div(
                #                     [
                #                         html.H6(
                #                             "WIND SPEED HISTOGRAM",
                #                             className="graph__title",
                #                         )
                #                     ]
                #                 ),
                #                 html.Div(
                #                     [
                #                         dcc.Slider(
                #                             id="bin-slider",
                #                             min=1,
                #                             max=60,
                #                             step=1,
                #                             value=20,
                #                             updatemode="drag",
                #                             marks={
                #                                 20: {"label": "20"},
                #                                 40: {"label": "40"},
                #                                 60: {"label": "60"},
                #                             },
                #                         )
                #                     ],
                #                     className="slider",
                #                 ),
                #                 html.Div(
                #                     [
                #                         dcc.Checklist(
                #                             id="bin-auto",
                #                             options=[
                #                                 {"label": "Auto", "value": "Auto"}
                #                             ],
                #                             value=["Auto"],
                #                             inputClassName="auto__checkbox",
                #                             labelClassName="auto__label",
                #                         ),
                #                         html.P(
                #                             "# of Bins: Auto",
                #                             id="bin-size",
                #                             className="auto__p",
                #                         ),
                #                     ],
                #                     className="auto__container",
                #                 ),
                #                 dcc.Graph(
                #                     id="wind-histogram",
                #                     figure=dict(
                #                         layout=dict(
                #                             plot_bgcolor=app_color["graph_bg"],
                #                             paper_bgcolor=app_color["graph_bg"],
                #                         )
                #                     ),
                #                 ),
                #             ],
                #             className="graph__container first",
                #         ),
                #         # wind direction
                #         html.Div(
                #             [
                #                 html.Div(
                #                     [
                #                         html.H6(
                #                             "WIND DIRECTION", className="graph__title"
                #                         )
                #                     ]
                #                 ),
                #                 dcc.Graph(
                #                     id="wind-direction",
                #                     figure=dict(
                #                         layout=dict(
                #                             plot_bgcolor=app_color["graph_bg"],
                #                             paper_bgcolor=app_color["graph_bg"],
                #                         )
                #                     ),
                #                 ),
                #             ],
                #             className="graph__container second",
                #         ),
                #     ],
                #     className="one-third column histogram__direction",
                # ),
            ],
            className="app__content",
        ),
    ],
    className="app__container",
)


def data_pull():
    # Connect to SQL database
    conn = psycopg2.connect(database='Weather', user=USER, password=PASS, host=HOST, port=PORT)

    # Define plot start date
    chart_cutoff = "'" + (datetime.datetime.now() - pd.Timedelta(days=7)).strftime('%Y/%m/%d %H:%M:%S') + "'"

    # Pull all data, within look back timeframe, into dataframe
    sql = 'SELECT "Time", "Temp" FROM weather_data WHERE weather_data."Time" > ' + chart_cutoff + ' ORDER BY weather_data."Time"'
    df = pd.read_sql(sql, conn)
    df['Time'] = pd.to_datetime(df['Time'])
    return df


# # Header data updates
# @app.callback(Output('live-update-text', 'children'),
#               Input('interval-component', 'n_intervals'))
# def update_metrics(n):
#     weather = data_pull()
#
#     time = 'Time: ' + str(weather['Time'].dt.strftime('%H:%M:%S').values[0])
#     status = 'Status: ' + str(weather['Status'].values[0])
#     temp = 'Temperature: ' + str(weather['Temp'].values[0]) + ' deg F'
#     humid = 'Humidity: ' + str(weather['Humid'].values[0]) + '%'
#     dew = 'Dew Point: ' + str(round(weather['Dew Point'], 2).values[0]) + ' deg F'
#     rain_rate = 'Rainfall Rate: ' + str(weather['Rainfall Rate'].values[0]) + '" per hour'
#     rain = 'Today' + "'" + 's Rainfall: ' + str(round(float(weather['Rainfall']), 2)) + '"'
#     press = 'Pressure: ' + str(round(weather['Pressure'], 2).values[0]) + ' inHg'
#
#     return time


# Quad chart update
@app.callback(Output('temp-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    weather = data_pull()

    trace = dict(
        type="scatter",
        x=weather['Time'],
        y=weather["Temp"],
        line={"color": "#42C4F7"},
        hoverinfo="skip",
        mode="lines",
    )

    layout = dict(
        plot_bgcolor=app_color["graph_bg"],
        paper_bgcolor=app_color["graph_bg"],
        font={"color": "#fff"},
        height=700,
        xaxis={
            "showline": True,
            "zeroline": False,
            "fixedrange": True,
            "title": "Date",
        },
        yaxis={
            "showgrid": True,
            "showline": True,
            "fixedrange": True,
            "zeroline": False,
            "gridcolor": app_color["graph_line"],
            'title': 'Temperature',
        },
    )

    return dict(data=[trace], layout=layout)


if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
