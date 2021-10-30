import os
import pandas as pd
from sqlalchemy import create_engine
import requests
from bs4 import BeautifulSoup
from pyowm import OWM
import datetime
import time

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

# Database credentials
USER = os.environ.get('DB_USER')
PASS = os.environ.get('DB_PASS')
PORT = os.environ.get('DB_PORT')

# Location data
CITY = os.environ.get('CITY')
RAIN_SITE = os.environ.get('RAIN_SITE')

# Establish connection with API
# SID = os.environ.get('TWILLIO_SID')
# TOK = os.environ.get('TWILLIO_TOK')
# TO = os.environ.get('TWILLIO_TO')
# FROM = os.environ.get('TWILLIO_FROM')
KEY = os.environ.get('OWM_API_KEY')
owm = OWM(KEY)
mgr = owm.weather_manager()

engine = create_engine('postgresql://' + USER + ':' + PASS + '@localhost:' + PORT + '/Weather')

while True:
    try:
        obs = mgr.weather_at_place(CITY)
        data = obs.weather

        # Retrieve weather data points
        t = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        temp = data.temperature(unit='fahrenheit')['temp']
        humid = data.humidity
        status = data.detailed_status
        dew_point = temp - (100 - humid) / 5
        pressure = data.pressure.get('press') * 0.029921

        rain_rate = data.rain.get('1h')
        if rain_rate is None:
            rain_rate = 0

        # Scrape rainfall data
        response = requests.get(RAIN_SITE,
                                headers={"User-Agent": "Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) "
                                                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 "
                                                       "Mobile Safari/537.36"})
        soup = BeautifulSoup(response.text, 'html.parser')
        rainfall = soup.find('div', id='homeStats').find_all('p')[5].text.split('"')[0]

        df = pd.DataFrame({'Time': [t],
                           'Temp': [temp],
                           'Humid': [humid],
                           'Dew Point': [dew_point],
                           'Rainfall Rate': [rain_rate],
                           'Rainfall': [rainfall],
                           'Pressure': [pressure],
                           'Status': [status]})

        df.to_sql(name='weather_data', con=engine, if_exists='append')
        print('Successful Scrape! ' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
        time.sleep(10)
    except:
        t = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        print('Warning! ' + str(t))
        # try:
        #     client = Client(SID, TOK)
        #     client.messages.create(to=TO,
        #                            from_=FROM,
        #                            body="There has been a problem while scraping Wx data at " + str(t))
        # except TwilioRestException as e:
        #     print('Text Failed at ' + str(t) + ': ' + str(e))
        #     continue
