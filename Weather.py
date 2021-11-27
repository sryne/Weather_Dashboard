import os
import datetime
import psycopg2
import pandas as pd
import dash
# from dash import dcc
import dash_core_components as dcc  # this is needed for headless mode
# from dash import html
import dash_html_components as html  # this is needed for headless mode
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from datetime import date

DATABASE_URL = os.environ['DATABASE_URL']
# USER = os.environ.get('DB_USER')
# PASS = os.environ.get('DB_PASS')
# HOST = os.environ.get('DB_HOST')
# PORT = os.environ.get('DB_PORT')

GRAPH_INTERVAL = os.environ.get("GRAPH_INTERVAL", 1000 * 10)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

server = app.server

app.title = 'Weather'

app_color = {"graph_bg": "#082255", "graph_line": "#007ACE"}


app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.H4("Weather Streaming", className="app__header__title"),

                        html.P(
                            "This app continually queries Open Weather Map API and scrapes another weather website",
                            className="app__header__title--grey",
                        ),

                        html.Div(
                            [
                                dcc.Dropdown(
                                    id='dropdown',
                                    options=[
                                        {'label': 'Temperature', 'value': 'Temp'},
                                        {'label': 'Humidity', 'value': 'Humid'},
                                        {'label': 'Dew Point', 'value': 'Dew Point'},
                                        {'label': 'Rainfall Rate', 'value': 'Rainfall Rate'},
                                        {'label': 'Daily Rainfall', 'value': 'Rainfall'},
                                        {'label': 'Pressure', 'value': 'Pressure'},
                                    ],
                                    value='Temp',
                                    clearable=False,
                                    searchable=False,
                                    style={'color': 'black'}
                                ),
                                html.Div(id='dd-output-container'),

                                dcc.DatePickerSingle(
                                    id='my-date-picker-single',
                                    min_date_allowed=date(2021, 10, 25),
                                    max_date_allowed=date(datetime.datetime.today().year,
                                                          datetime.datetime.today().month,
                                                          datetime.datetime.today().day),
                                    date=(datetime.datetime.now() - pd.Timedelta(days=7)).strftime('%Y/%m/%d %H:%M:%S')
                                ),
                                html.Div(id='output-container-date-picker-single')
                            ],
                            className='dropdown',
                        ),
                    ],
                    className="app__header__desc",
                ),
            ],
            className="app__header",
        ),

        html.Div(
            [
                html.Div(
                    [

                        html.Div(
                            [
                                html.P('Current Time', id='live-time', className='graph__title'),
                                html.P('Current Status', id='live-status', className='graph__title'),
                                html.P('Current Temp', id='live-temp', className='graph__title'),
                                html.P('Current humid', id='live-humid', className='graph__title'),
                                html.P('Current Dew Point', id='live-dew', className='graph__title'),
                                html.P('Current Rainfall Rate', id='live-rain-rate', className='graph__title'),
                                html.P('Daily Rainfall', id='live-rain', className='graph__title'),
                                html.P('Current Pressure', id='live-press', className='graph__title'),
                            ],
                        ),

                        dcc.Interval(
                            id="interval-data",
                            interval=int(GRAPH_INTERVAL),
                            n_intervals=0,
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
                            id="interval-fig",
                            interval=int(GRAPH_INTERVAL),
                            n_intervals=0,
                        ),
                    ],
                    className="three-thirds column temp__container",
                ),
            ],
            className="app__content",
        ),
    ],
    className="app__container",
)


def data_pull(cutoff):
    # Connect to SQL database
    # conn = psycopg2.connect(database='Weather', user=USER, password=PASS, host=HOST, port=PORT)
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    # Define plot start date
    cutoff = "'" + (pd.to_datetime(cutoff).strftime('%Y/%m/%d %H:%M:%S')) + "'"

    # Pull all data, within look back timeframe, into dataframe
    sql = 'SELECT * FROM weather_data WHERE weather_data."Time" > ' + cutoff + ' ORDER BY weather_data."Time"'
    df = pd.read_sql(sql, conn)
    df['Time'] = pd.to_datetime(df['Time'])
    return df


@app.callback(Output('live-time', 'children'),
              Output('live-status', 'children'),
              Output('live-temp', 'children'),
              Output('live-humid', 'children'),
              Output('live-dew', 'children'),
              Output('live-rain-rate', 'children'),
              Output('live-rain', 'children'),
              Output('live-press', 'children'),
              [
                  Input('interval-data', 'n_intervals'),
                  Input('my-date-picker-single', 'date')
              ]
              )
def current_data(n, date):
    weather = data_pull(cutoff=date)
    time = 'Current Time: ' + str(weather['Time'].dt.strftime('%H:%M:%S').values[-1])
    status = 'Status: ' + str(weather['Status'].values[-1])
    temp = 'Temperature: ' + str(weather['Temp'].values[-1]) + ' deg F'
    humid = 'Humidity: ' + str(weather['Humid'].values[-1]) + '%'
    dew = 'Dew Point: ' + str(round(weather['Dew Point'], 2).values[-1]) + ' deg F'
    rain_rate = 'Rainfall Rate: ' + str(weather['Rainfall Rate'].values[-1]) + '" per hour'
    rain = 'Today' + "'" + 's Rainfall: ' + str(weather['Rainfall'].values[-1]) + '"'
    press = 'Pressure: ' + str(round(weather['Pressure'], 2).values[-1]) + ' inHg'
    return time, status, temp, humid, dew, rain_rate, rain, press


@app.callback(Output('temp-graph', 'figure'),
              [
                  Input('interval-fig', 'n_intervals'),
                  Input('dropdown', 'value'),
                  Input('my-date-picker-single', 'date')
              ]
              )
def update_graph_live(n, value, date):
    weather = data_pull(cutoff=date)

    trace = dict(
        type="scatter",
        x=weather['Time'],
        y=weather[value],
        line={"color": "#42C4F7"},
        hoverinfo="skip",
        mode="lines",
    )

    layout = dict(
        plot_bgcolor=app_color["graph_bg"],
        paper_bgcolor=app_color["graph_bg"],
        font={"color": "#fff"},
        height=400,
        margin=dict(l=75, r=20, t=20, b=75),
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
            'title': value,
        },
    )

    return dict(data=[trace], layout=layout)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=False, threaded=True)
