# WeatherBot
Raspberry Pi Zero + E-Ink + Tomorrow.io = ❤️

First, sign up for a free account for a Tomorrow.IO and get your API key. 
For free, you get 500 calls a day. You can adjust the schedule task range in the main.py file towards the bottom. 

Once you have your API key. You need to install the requriements.
> pip3 install -r requirements.txt

Once done, run the script with python3 main.py. This will generate the settings.ini file. 
Enter the API key, lat, and long. 

Once done, you can run the script again. As long as debug = True, it will display output text.

Add the script to crontab -e
> @reboot   sleep 60 && cd /path/to/project/ && /usr/bin/python3 main.py &

Credits:

Icons:
[Bluxart](https://www.iconfinder.com/Bluxart) - [Meteocons Icon Pack](https://www.iconfinder.com/iconsets/meteocons)
