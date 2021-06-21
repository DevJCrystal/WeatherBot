import os
import glob
import time
import json
import requests 
import schedule
import configparser

from datetime import datetime as dt
from PIL import Image, ImageFont, ImageDraw

using_screen = True

try:
    from lib.waveshare_epd import epd2in13_V2
except:
    using_screen = False
    print('Failed to import Waveshare')

# Debug
count = 0
debug_mode = True

# Screen
full_update_needed = False
full_update_enabled = False

# Static information
if os.path.exists('settings.ini'):
    Config = configparser.ConfigParser()
    Config.read("settings.ini")
else:
    f = open('settings.ini', 'w')
    f.write('[Api]\n')
    f.write('Key=\n')
    f.write('\n')
    f.write('[Location]\n')
    f.write('Lat=\n')
    f.write('Long=\n')
    f.close()
    print('Please fill out the settings file!')
    exit()

# Windows vs unix
slash = '\\' if os.name == 'nt' else '/'

if using_screen:
    try:
        epd = epd2in13_V2.EPD()
    except:
        print('Error init screen.')

# Load icons once to prevent leaks
dict_of_images = {}
list_of_images = glob.glob(f"ico{slash}*.png")
blank_image = Image.new('1', (250, 122), 255)  # Blank image

for image in list_of_images:
    dict_of_images[image] = Image.open(image)

# Woodbury - CompuWeigh
location = f"{Config.get('Location', 'Lat')},{Config.get('Location', 'Long')}"

# Sign up for a free account at tomorrow.io - 500 free calls a day
apiKey = Config.get('Api', 'Key')
if len(apiKey) == 0:
    print('No apiKey installed! - Check ~ line 50')
    quit()

# Fonts
font_16 = ImageFont.truetype('Font.ttc', 16)
font_20 = ImageFont.truetype('LeagueSpartan-Bold.otf', 20)
font_24 = ImageFont.truetype('LeagueSpartan-Bold.otf', 24)

class LocalStation:
    def __init__(self) -> None:
        self.alerts = False
        self.tempeture = 99
        self.wind_speed = 99
        self.weather_code = 0
        self.wind_direction = 0
        self.precipitation_probability = 0

    def update_weather_data(self):
        global full_update_needed

        # Current weather
        try:
            updated_data = get_current_weather()

            # We only want to force an update if there really is an update.
            full_update_needed = True if self.tempeture == updated_data.get('temperature') else full_update_needed
            full_update_needed = True if self.weather_code == updated_data.get('weatherCode') else full_update_needed
            full_update_needed = True if self.precipitation_probability == updated_data.get('precipitationProbability') else full_update_needed
            
            self.wind_speed = updated_data.get('windSpeed')
            self.tempeture = updated_data.get('temperature')
            self.weather_code = updated_data.get('weatherCode')
            self.wind_direction = updated_data.get('windDirection')
            self.precipitation_probability = updated_data.get('precipitationProbability')

        except:
            print('There was an error updateing the data!')

    def update_alert_data(self):

        global full_update_needed

        try:
            alert_data = check_for_alerts()

            # If there are any alerts, show alert text
            if len(alert_data['data'].get('events')) > 0:

                # If we weren't already showing the text, show it!
                if not self.alerts:
                    self.alerts = True
                    full_update_needed = True
            else:
                # If there is no longer an alert, hide it!
                if self.alerts:
                    self.alerts = False
                    full_update_needed = True
            
        except:
            print('There was an error updating the alert(s)')
            try:
                # This message shows when there is an error with the API
                alert_data['message']
                print('Alert: ' + alert_data['message'])
            except:
                pass
        

# If window (nt) then cls else clear (mac / linux)
def clear():
    _ = os.system('cls' if os.name == 'nt' else 'clear')

# VOODOO Script - I really want to take the time to understand this.
# https://codegolf.stackexchange.com/questions/21927/convert-degrees-to-one-of-the-32-points-of-the-compass/196617#196617

z=int
direction = {'North':'N','East':'E','South':'S','West':'W'}

def a(t,d,l):
    for i,j in d.items():
        if l:i=i.lower()
        t=t.replace(i,j)
    return t

def b(h):
    p=32;r=360;h=(h+(r/p/2))/(r/p);j=z(z(z(h%8)%8/(p/p))*p/p);h=z(h/8)%4;k=direction.keys();u=['W','W by x','W-z','Z by w','Z','Z by x','X-z','X by w'];d={'W':list(k)[h],'X':list(k)[(h+1)%4]};d['w']=d['W'].lower();d['x']=d['X'].lower();d['Z']=d['W']+d['x']if(d['W']=='North'or d['W']=='South') else d['X']+d['w'];d['z']=d['Z'].lower();return a(u[j],d,0)

# End of VOODOO - Carry on

# I added this to make it a little less confusing. 
def return_wind_direction(d):
    return (a(a(a(b(d),direction,0),direction,1),{'by':'b',' ':'','-':''},0))

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

# TODO 
# Get day/night
# Adjust code to match day/night icons.

# I have adjusted most of these names as heavy rain and light rain is still rain. Too much text. 
def code_to_weather(code):
    weatherCodeDeCoder = {
        0:    "Unknown",
        1000: "Clear", 1100: "Mostly_Clear",
        1001: "Cloudy", 1101: "Partly_Cloudy", 1102: "Mostly_Cloudy",
        2000: "Fog", 2100: "Fog",
        3000: "Windy", 3001: "Windy", 3002: "Windy",
        4000: "Rain", 4001: "Rain", 4200: "Rain", 4201: "Rain",
        5000: "Snow", 5001: "Snow", 5100: "Snow", 5101: "Snow",
        6000: "Freezing_Rain", 6001: "Freezing_Rain", 6200: "Freezing_Rain", 6201: "Freezing_Rain",
        7000: "Ice_Pellets", 7101: "Ice_Pellets", 7102: "Ice_pellets",
        8000: "Thunderstorm"
    }

    return weatherCodeDeCoder.get(int(code))

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

def update_display(local_weather):
    global count
    global full_update_needed
    global full_update_enabled

    timeOfDay = dt.now()
    d = timeOfDay.strftime("%a %b %d, %Y\n%I:%M:%S %p")

    if debug_mode:
        clear()
        count+=1
        print(count)
        print(f'Full Update? {full_update_needed}')
        print(f'Show Alarm: {local_weather.alerts}')
        print(f'Screen Update Mode: (T=Full F=Part) {full_update_enabled}')
        print('-'*20) # Makes 20 dashes, fancy!
        print(d)
        print(f'Temp: {str(round(local_weather.tempeture))}°F')
        print(f'Wind Speed: {local_weather.wind_speed} Wind Direction: {local_weather.wind_direction}')
        print(f'Precipitation Probability: {local_weather.precipitation_probability}')
        print(f'ico{slash}{code_to_weather(local_weather.weather_code)}.png')
        print(f'Current conditions: {code_to_weather(local_weather.weather_code).replace("_"," ")}')

    # Create blank image
    image = blank_image.copy()
    draw = ImageDraw.Draw(image)

    # Top left - Date and Time
    draw.text((2, 0), d, font = font_16, fill = 0)

    # Left Mid - Alarm
    if local_weather.alerts:
        draw.rectangle([(1,42),(75,66)],fill = 0)
        draw.text((2, 45), u'ALERT!', font = font_20, fill = 1)

    # Left Mid - Wind and Direction
    draw.text((2, 70), f'W: {round(local_weather.wind_speed)} MPH | D: {return_wind_direction(local_weather.wind_direction)}', font = font_16, fill = 0)

    # Bottom Left - Current weather condition
    draw.text((2, 100), code_to_weather(local_weather.weather_code).replace("_"," "), font = font_20, fill = 0)

    # Load weather icon
    imgIco = dict_of_images[f'ico{slash}{code_to_weather(local_weather.weather_code)}.png']

    # Top Right - Insert weather icon
    image.paste(imgIco, (185,0), imgIco)

    # Precipitation allignment correction
    space = ''
    if len(str(round(local_weather.precipitation_probability))) == 1:
        space = '   '
    elif len(str(round(local_weather.precipitation_probability))) == 2:
        space = ' '
    else:
        space = ''

    # Right Mid - Precipitation
    draw.text((188, 70), f'P: {space}{str(round(local_weather.precipitation_probability))} %', font = font_16, fill = 0)

    # Bottom Right - Large Temp
    draw.text((180, 95), ' ' + str(round(local_weather.tempeture)) + '°F', font = font_24, fill = 0)

    # Correct oreintation
    image = image.rotate(180)

    if debug_mode:
        print('End of image creation!')

    # Prepare screen
    try:

        if using_screen:
            if debug_mode:
                print('Starting epd!')
            
            if full_update_needed:
                if not full_update_enabled:
                    epd.init(epd.FULL_UPDATE)
                    full_update_enabled = True

                epd.Clear(0xFF)
                epd.displayPartBaseImage(epd.getbuffer(image))

                # Prevent looping full updates
                full_update_needed = False
            else:
                if full_update_enabled:
                    epd.init(epd.PART_UPDATE)
                    full_update_enabled = False

                epd.displayPartial(epd.getbuffer(image))
    except Exception as e:
        print('There was an error updating the screen.')
        input(e)

def startUp():
    global full_update_enabled

    try:
        if not full_update_enabled:
            epd.init(epd.FULL_UPDATE)
            full_update_enabled = True

        epd.Clear(0xFF)
        epd.display(epd.getbuffer(blank_image))
    except:
        print('Could not clear screen on startup.')

if __name__ == "__main__":

    startUp()
    local_weather = LocalStation()

    update_display(local_weather)

    # Get some data so it isn't null and update display
    local_weather.update_alert_data()
    local_weather.update_weather_data()

    schedule.every(5).to(15).minutes.do(local_weather.update_alert_data)
    schedule.every(5).to(15).minutes.do(local_weather.update_weather_data)

    while True:
        update_display(local_weather)
        time.sleep(1)
        schedule.run_pending()