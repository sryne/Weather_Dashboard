import os
from datetime import datetime
import copy
import datetime
import psycopg2
import pandas as pd
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from dash.dependencies import Input, Output

USER = os.environ.get('DB_USER')
PASS = os.environ.get('DB_PASS')
HOST = os.environ.get('DB_HOST')
PORT = os.environ.get('DB_PORT')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    html.Div([
        html.H4('Current Weather'),
        html.Div(id='live-update-text'),
        dcc.Graph(id='live-update-graph',
                  figure={'layout': {'height': 850}}),
        dcc.Interval(
            id='interval-component',
            interval=10 * 1000,  # in milliseconds
            n_intervals=0
        )
    ])
)


# Header data updates
@app.callback(Output('live-update-text', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    # Connect to SQL database
    conn = psycopg2.connect(database='Weather',
                            user=USER,
                            password=PASS,
                            host=HOST,
                            port=PORT)

    # Pull all data, within look back timeframe, into dataframe
    sql = 'SELECT * FROM weather_data order by weather_data."Time" DESC LIMIT 1'
    df = pd.read_sql(sql, conn)
    df['Time'] = pd.to_datetime(df['Time'])

    print('*******Ribbon Refreshed*******')

    style = {'padding': '5px', 'fontSize': '16px'}
    return [
        html.Span('Time: ' + str(df['Time'].dt.strftime('%H:%M:%S').values[0]), style=style),
        html.Span('Status: ' + str(df['Status'].values[0]), style=style),
        html.Span('Temperature: ' + str(df['Temp'].values[0]) + ' deg F', style=style),
        html.Span('Humidity: ' + str(df['Humid'].values[0]) + '%', style=style),
        html.Span('Dew Point: ' + str(round(df['Dew Point'], 2).values[0]) + ' deg F', style=style),
        html.Span('Rainfall Rate: ' + str(df['Rainfall Rate'].values[0]) + '" per hour', style=style),
        html.Span('Today' + "'" + 's Rainfall: ' + str(round(float(df['Rainfall']), 2)) + '"', style=style),
        html.Span('Pressure: ' + str(round(df['Pressure'], 2).values[0]) + ' inHg', style=style)
    ]


# Quad chart update
@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    # Connect to SQL database
    conn = psycopg2.connect(database='Weather',
                            user=USER,
                            password=PASS,
                            host=HOST,
                            port=PORT)

    # Define plot start date
    chart_cutoff = "'" + (datetime.datetime.now() - pd.Timedelta(days=7)).strftime('%Y/%m/%d %H:%M:%S') + "'"

    # Pull all data, within look back timeframe, into dataframe
    sql = 'SELECT * FROM weather_data WHERE weather_data."Time" > ' + chart_cutoff + ' ORDER BY weather_data."Time"'
    df = pd.read_sql(sql, conn)
    df['Time'] = pd.to_datetime(df['Time'])

    # Create the graph with subplots
    fig = plotly.subplots.make_subplots(rows=2, cols=2, vertical_spacing=0.1, horizontal_spacing=0.05)
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 10
    }
    fig['layout']['legend'] = {'xanchor': 'left'}

    fig.update_layout({'plot_bgcolor': 'rgba(0,0,0,0)',
                       'paper_bgcolor': 'rgba(0,0,0,0)'})

    fig.append_trace({
        'x': df['Time'],
        'y': df['Temp'],
        'name': 'Temperature',
        'mode': 'lines',
        'type': 'scatter'
    }, 1, 1)
    fig.append_trace({
        'x': df['Time'],
        'y': df['Dew Point'],
        'name': 'Dew Point',
        'mode': 'lines',
        'type': 'scatter'
    }, 1, 1)
    fig.append_trace({
        'x': df['Time'],
        'y': df['Humid'],
        'name': 'Humidity',
        'mode': 'lines',
        'type': 'scatter'
    }, 2, 1)
    fig.append_trace({
        'x': df['Time'],
        'y': df['Rainfall Rate'],
        'name': 'Rainfall Rate',
        'mode': 'lines',
        'type': 'scatter'
    }, 1, 2)
    fig.append_trace({
        'x': df['Time'],
        'y': df['Rainfall'],
        'name': 'Rainfall',
        'mode': 'lines',
        'type': 'scatter'
    }, 1, 2)
    fig.append_trace({
        'x': df['Time'],
        'y': df['Pressure'],
        'name': 'Pressure',
        'mode': 'lines',
        'type': 'scatter'
    }, 2, 2)

    print('*******Chart Refreshed*******')

    return fig


if __name__ == '__main__':
    app.server.run(debug=False, threaded=True)
