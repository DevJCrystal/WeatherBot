from epd import display_io
from epd.lib.waveshare_epd import epd2in13bc

from PIL import Image, ImageFont, ImageDraw

class Display:
    def __init__(self) -> None:
        self.epd = epd2in13bc.EPD()
        self.epd.init()
        self.blank_image = Image.new('1', (self.epd.height, self.epd.width), 255)

        self.font_14 = ImageFont.truetype(display_io.default_font, 14)
        self.font_16 = ImageFont.truetype(display_io.default_font, 16)
        self.font_18 = ImageFont.truetype(display_io.accent_font, 18)
        self.font_20 = ImageFont.truetype(display_io.accent_font, 20)
        self.font_24 = ImageFont.truetype(display_io.accent_font, 24)

    def update_display(self, local_weather):

        # The update speed of this screen is to slow for me to 
        # want it to update every couple of seconds.

        if local_weather.full_update_needed:

            d = display_io.time_return(False)
            display_io.debug_text(local_weather, False)

            try:
                # Create blank image
                black_image = self.blank_image.copy()
                black_draw = ImageDraw.Draw(black_image)

                red_image = self.blank_image.copy()
                red_draw = ImageDraw.Draw(red_image)

                # Top left - Date and Time
                black_draw.text((2, 0), d, font = self.font_16, fill = 0)

                # Left Mid - Alarm
                if local_weather.alerts:
                    red_draw.rectangle([(1,20),(75,44)],fill = 0)
                    red_draw.text((5, 23), u'ALERT!', font = self.font_18, fill = 1)

                # Left Mid - Wind and Direction
                black_draw.text((2, 62), f'W: {round(local_weather.wind_speed)} MPH | D: {display_io.return_wind_direction(local_weather.wind_direction)}', font = self.font_14, fill = 0)

                # Bottom Left - Current weather condition
                black_draw.text((2, 82), display_io.code_to_weather(local_weather.weather_code).replace("_"," "), font = self.font_18, fill = 0)

                # Load weather icon
                imgIco = display_io.get_icon(local_weather.weather_code, local_weather.sunrise, local_weather.sunset)[0]

                # Top Right - Insert weather icon
                black_image.paste(imgIco, (145,0), imgIco)

                # Precipitation allignment correction
                space = ''
                if len(str(round(local_weather.precipitation_probability))) == 1:
                    space = '   '
                elif len(str(round(local_weather.precipitation_probability))) == 2:
                    space = ' '
                else:
                    space = ''
                    
                # Bottom Mid Left
                black_draw.text((2, 45), f'P: {space}{str(round(local_weather.precipitation_probability))} %', font = self.font_16, fill = 0)

                # Bottom Right - Large Temp
                black_draw.text((160, 82), ' ' + str(round(local_weather.tempeture)) + '°F', font = self.font_18, fill = 0)

                # Correct oreintation
                if local_weather.flip_image:
                    black_image = black_image.rotate(180)
                    red_image = red_image.rotate(180)

                self.epd.Clear()
                self.epd.display(self.epd.getbuffer(black_image),self.epd.getbuffer(red_image))
                local_weather.full_update_needed = False

            except Exception as e:
                print('There was an error updating the screen.')
                input(e)