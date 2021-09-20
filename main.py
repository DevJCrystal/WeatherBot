import os
import time
import json
import logging
import requests
import schedule
import configparser
from epd import base
from datetime import datetime as dt, timezone

# Static information

# Windows vs unix
slash = '\\' if os.name == 'nt' else '/'

now = dt.now()
dt_string = now.strftime("%m_%d_%y_%I_%M_%S")
logging.basicConfig(filename=f'logs{slash}error_log_{dt_string}.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

if os.path.exists('settings.ini'):
    Config = configparser.ConfigParser()
    Config.read("settings.ini")
    logging.info('Read settings file!')
else:
    f = open('settings.ini', 'w')
    f.write('[API]\n')
    f.write('Key=\n')
    f.write('Message=Tomorrow gives 500 free calls a day and 25 an hour.')
    f.write('Alert_Time_Check_Range=10,15\n')
    f.write('Current_Weather_Time_Check_Range=10,15\n')
    f.write('\n')
    f.write('[Location]\n')
    f.write('Lat=\n')
    f.write('Long=\n')
    f.write('\n')
    f.write('[Application_Settings]\n')
    f.write('Screen_Type=\n')
    f.write('Save_Image=False\n')
    f.write('Flip_Image=True\n')
    f.close()
    logging.info('Please fill out the settings file!')
    exit()

try:
    epd = base.Get_Display(Config.get('Application_Settings', 'Screen_Type'))
except Exception as e:
    logging.error('Failed to load screen')
    print(e)
    logging.info('Waiting 5 seconds before running text/image only mode.')

    time.sleep(5)

    from epd import text_image_only
    epd = text_image_only.Display()

# Sign up for a free account at tomorrow.io - 500 free calls a day
apiKey = Config.get('API', 'Key')
if len(apiKey) == 0:
    logging.critical('No apiKey installed! - Go into settings!')
    quit()

# Loading location from Settings
location = f"{Config.get('Location', 'Lat')},{Config.get('Location', 'Long')}"

class LocalStation:
    def __init__(self) -> None:

        self.save_image = Config.get('Application_Settings', 'Save_Image')
        self.flip_image = Config.get('Application_Settings', 'Flip_Image')

        self.alerts = False

        self.sunset = None
        self.sunrise = None

        self.tempeture = 0
        self.wind_speed = 0
        self.weather_code = 0
        self.wind_direction = 0
        self.last_update_data = None
        self.full_update_needed = True
        self.full_update_enabled = True
        self.precipitation_probability = 0

    def update_weather_data(self):
        self.full_update_needed

        # Current weather
        try:
            updated_data = get_current_weather()

            # We only want to force an update if there really is an update.
            self.full_update_needed = True if self.tempeture == updated_data.get('temperature') else self.full_update_needed
            self.full_update_needed = True if self.weather_code == updated_data.get('weatherCode') else self.full_update_needed
            self.full_update_needed = True if self.precipitation_probability == updated_data.get('precipitationProbability') else self.full_update_needed

            self.last_update_data = updated_data

            self.wind_speed = updated_data.get('windSpeed')
            self.tempeture = updated_data.get('temperature')
            self.weather_code = updated_data.get('weatherCode')
            self.wind_direction = updated_data.get('windDirection')
            self.precipitation_probability = updated_data.get('precipitationProbability')

        except:
            logging.error('There was an error updating the data!')

    def update_alert_data(self):

        try:
            alert_data = check_for_alerts()

            # If there are any alerts, show alert text
            if len(alert_data['data'].get('events')) > 0:

                # If we weren't already showing the text, show it!
                if not self.alerts:
                    self.alerts = True
                    self.full_update_needed = True

            else:
                # If there is no longer an alert, hide it!
                if self.alerts:
                    self.alerts = False
                    self.alert_type = ""
                    self.full_update_needed = True

        except:
            logging.error('There was an error updating the alert(s)')
            try:
                # This message shows when there is an error with the API
                alert_data['message']
                print('Alert: ' + alert_data['message'])
            except:
                pass

    def update_local_times(self):

        data = update_sun_time()

        sunset = data['results']['sunset'].replace("T", " ").split("+")[0]
        sunrise = data['results']['sunrise'].replace("T", " ").split("+")[0]

        self.sunset = utc_to_now(sunset)
        self.sunrise = utc_to_now(sunrise)

def get_current_weather():

    url = "https://api.tomorrow.io/v4/timelines"

    querystring = {
                "location": location,
                "units":"imperial",
                "timesteps":"current",
                "fields": ["temperature",
                        "windSpeed",
                        "windDirection",
                        "weatherCode",
                        "precipitationProbability"],
                "apikey":apiKey
                }

    headers = {"Accept": "application/json"}

    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
    except:
        logging.error('Could not get data!')
        # TODO try pinging an address to check to see if there is internet.
        # If there is no internet, try rebooting.

    try:
        json_response = json.loads(response.text)
    except:
        logging.error('Invalid json response!')
        logging.error('--Start of Response--')
        logging.error(response)
        logging.error('--End of Response--')
        return ['Error', response]

    return json_response['data']['timelines'][0]['intervals'][0].get('values')

# Check for any alerts of wind/floods/tornado/thunderstorm type
# Buffer is area around location in km (metric)
def check_for_alerts():

    url = "https://api.tomorrow.io/v4/events"

    querystring = {
        "location":location,
        "insights":
        ["wind",
        "floods",
        "tornado",
        "thunderstorms"],
        "buffer":"10",
        "apikey":apiKey
        }

    headers = {"Accept": "application/json"}

    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
    except:
        logging.error('Could not get data!')
        # TODO try pinging an address to check to see if there is internet.
        # If there is no internet, try rebooting.

    try:
        json_response = json.loads(response.text)
    except:
        logging.error('Invalid json response!')
        logging.error('--Start of Response--')
        logging.error(response)
        logging.error('--End of Response--')
        return ['Error', response]

    return json_response

def update_sun_time():
    url = "https://api.sunrise-sunset.org/json"

    querystring = {
                "lat": location.split(",")[0],
                "lng": location.split(",")[1],
                "formatted":0
                }

    headers = {"Accept": "application/json"}

    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
    except:
        logging.error('Could not get data!')
        # TODO try pinging an address to check to see if there is internet.
        # If there is no internet, try rebooting.
    return json.loads(response.text)

def utc_to_now(utc_time):
        datetime_object = dt.strptime(utc_time, '%Y-%m-%d %H:%M:%S')
        time = datetime_object.replace(tzinfo=timezone.utc).astimezone(tz=None)

        return str(time)[:-6]

if __name__ == "__main__":

    # Load the weather class
    local_weather = LocalStation()

    # Get some fresh data while it is still hot
    local_weather.update_alert_data()
    local_weather.update_local_times()
    local_weather.update_weather_data()

    # Display the first image!
    epd.update_display(local_weather)

    # Configure schedule tasks!
    schedule.every().day.at("00:00").do(local_weather.update_local_times)

    temp = Config.get('API', 'Alert_Time_Check_Range').split(',')
    schedule.every(int(temp[0])).to(int(temp[1])).minutes.do(local_weather.update_alert_data)

    temp = Config.get('API', 'Current_Weather_Time_Check_Range').split(',')
    schedule.every(int(temp[0])).to(int(temp[1])).minutes.do(local_weather.update_weather_data)

    if epd.scrub_needed:
        # This is to prevent screen burn in. 
        # I have seen it on two screens.
        schedule.every().hour.do(epd.Scrub)
        local_weather.full_update_needed = True

    while True:

        time.sleep(1)
        schedule.run_pending()

        try:
            epd.update_display(local_weather)
        except Exception as e:
            logging.critical(e)
