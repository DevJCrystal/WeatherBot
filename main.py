import os
import time
import json
import requests 
import schedule
import configparser
from epd import base

# Static information
if os.path.exists('settings.ini'):
    Config = configparser.ConfigParser()
    Config.read("settings.ini")
else:
    f = open('settings.ini', 'w')
    f.write('[API]\n')
    f.write('Key=\n')
    f.write('\n')
    f.write('[Location]\n')
    f.write('Lat=\n')
    f.write('Long=\n')
    f.write('\n')
    f.write('[Application_Settings]\n')
    f.write('Screen_Type=\n')
    f.close()
    print('Please fill out the settings file!')
    exit()

try:
    epd = base.Get_Display(Config.get('Application_Settings', 'Screen_Type'))
except Exception as e:
    print('Failed to import Screen')
    print(e)
    print('Waiting 5 seconds before running text/image only mode.')
    
    time.sleep(5)

    from epd import text_image_only
    epd = text_image_only.Display()

# Sign up for a free account at tomorrow.io - 500 free calls a day
apiKey = Config.get('API', 'Key')
if len(apiKey) == 0:
    print('No apiKey installed! - Go into settings!')
    quit()

# Loading location from Settings
location = f"{Config.get('Location', 'Lat')},{Config.get('Location', 'Long')}"

class LocalStation:
    def __init__(self) -> None:
        
        self.alerts = False

        self.tempeture = 0
        self.wind_speed = 0
        self.weather_code = 0
        self.wind_direction = 0
        self.save_image = False
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
            print('There was an error updateing the data!')

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
            print('There was an error updating the alert(s)')
            try:
                # This message shows when there is an error with the API
                alert_data['message']
                print('Alert: ' + alert_data['message'])
            except:
                pass

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

    response = requests.request("GET", url, headers=headers, params=querystring)

    json_response = json.loads(response.text)

    try:
        json_response['message']
        return ['Error', json_response['message']]
    except:
        pass

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

    response = requests.request("GET", url, headers=headers, params=querystring)

    return json.loads(response.text)

if __name__ == "__main__":

    # Load the weather class
    local_weather = LocalStation()

    # Get some fresh data while it is still hot
    local_weather.update_alert_data()
    local_weather.update_weather_data()

    # Display the first image!
    epd.update_display(local_weather)


    # Configure schedule tasks!
    temp = Config.get('API', 'Alert_Time_Check_Range').split(',')
    schedule.every(int(temp[0])).to(int(temp[1])).minutes.do(local_weather.update_alert_data)

    temp = Config.get('API', 'Current_Weather_Time_Check_Range').split(',')
    schedule.every(int(temp[0])).to(int(temp[1])).minutes.do(local_weather.update_weather_data)

    while True:

        time.sleep(1)
        schedule.run_pending()

        epd.update_display(local_weather)