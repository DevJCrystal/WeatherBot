import os, glob
from datetime import datetime as dt

from PIL import Image

# Windows vs unix
slash = '\\' if os.name == 'nt' else '/'

default_font = "fonts/Font.ttc"
accent_font  = "fonts/LeagueSpartan-Bold.otf"

# Load icons once to prevent leaks
dict_of_images = {}
list_of_images = glob.glob(f"ico{slash}*.png")

for image in list_of_images:
    dict_of_images[image] = Image.open(image)

def time_return(full_string):
    time_of_day = dt.now()
    time_string = '%a %b %d, %Y\n%I:%M:%S %p' if full_string else '%a %b %d, %Y'
    d = time_of_day.strftime(time_string)

    return d

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

def get_icon(weather_code, sunrise, sunset):
    # Get current time
    time_of_day = dt.now()
    time_string = '%Y-%m-%d %I:%M:%S'
    d = time_of_day.strftime(time_string)

    night_str = ""

    if d > sunrise and d < sunset:
        night_str = ""
    else:
        night_str = "_N"

    return (dict_of_images[f'ico{slash}{code_to_weather(weather_code)}{night_str}.png'].convert("RGBA"), f'ico{slash}{code_to_weather(weather_code)}{night_str}.png')

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

def debug_text(local_weather, full_timestamp):
    
    clear()
    print(f'Full Update Enabled: {local_weather.full_update_enabled}')
    print(f'Full Update  Needed: {local_weather.full_update_needed}')
    print('-'*20)
    print(time_return(full_timestamp))
    print(f'Sunrise: {local_weather.sunrise}')
    print(f'Sunset : {local_weather.sunset}')
    print(f'Show Alarm: {local_weather.alerts}')
    print('-'*20)
    print(f'Temp: {str(round(local_weather.tempeture))}°F')
    print(f'Wind Speed: {local_weather.wind_speed} Wind Direction: {return_wind_direction(local_weather.wind_direction)}')
    print(f'Precipitation Probability: {local_weather.precipitation_probability}')
    print(f'{get_icon(local_weather.weather_code, local_weather.sunrise, local_weather.sunset)[1]}')
    print(f'Current conditions: {code_to_weather(local_weather.weather_code).replace("_"," ")}')
