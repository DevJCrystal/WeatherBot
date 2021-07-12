from epd import display_io
from epd.lib.waveshare_epd import epd2in13_V2

from PIL import Image, ImageFont, ImageDraw

class Display:
    def __init__(self) -> None:
        self.epd = epd2in13_V2.EPD()
        self.epd.init(self.epd.FULL_UPDATE)
        self.blank_image = Image.new('1', (self.epd.height, self.epd.width), 255)

        self.font_14 = ImageFont.truetype('Font.ttc', 14)
        self.font_16 = ImageFont.truetype('Font.ttc', 16)
        self.font_18 = ImageFont.truetype('LeagueSpartan-Bold.otf', 18)
        self.font_20 = ImageFont.truetype('LeagueSpartan-Bold.otf', 20)
        self.font_24 = ImageFont.truetype('LeagueSpartan-Bold.otf', 24)

    def update_display(self, local_weather):

        d = display_io.time_return(True)
        display_io.debug_text(local_weather, True)

        try:

            # Create blank image
            image = self.blank_image.copy()
            draw = ImageDraw.Draw(image)

            # Top left - Date and Time
            draw.text((2, 0), d, font = self.font_16, fill = 0)

            # Left Mid - Alarm
            if local_weather.alerts:
                draw.rectangle([(1,42),(75,66)],fill = 0)
                draw.text((2, 45), u'ALERT!', font = self.font_20, fill = 1)

            # Left Mid - Wind and Direction
            draw.text((2, 70), f'W: {round(local_weather.wind_speed)} MPH | D: {display_io.return_wind_direction(local_weather.wind_direction)}', font = self.font_16, fill = 0)

            # Bottom Left - Current weather condition
            draw.text((2, 100), display_io.code_to_weather(local_weather.weather_code).replace("_"," "), font = self.font_20, fill = 0)

            # Load weather icon
            imgIco = display_io.get_icon(local_weather.weather_code, local_weather.sunrise, local_weather.sunset)[0]

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
            draw.text((188, 70), f'P: {space}{str(round(local_weather.precipitation_probability))} %', font = self.font_16, fill = 0)

            # Bottom Right - Large Temp
            draw.text((180, 95), ' ' + str(round(local_weather.tempeture)) + '°F', font = self.font_24, fill = 0)

            # Correct oreintation
            image = image.rotate(180)

            # Prepare screen
                
            if local_weather.full_update_needed:
                if not local_weather.full_update_enabled:
                    self.epd.init(self.epd.FULL_UPDATE)
                    local_weather.full_update_enabled = True

                self.epd.Clear(0xFF)
                self.epd.displayPartBaseImage(self.epd.getbuffer(image))

                # Prevent looping full updates
                local_weather.full_update_needed = False
            else:
                if local_weather.full_update_enabled:
                    self.epd.init(self.epd.PART_UPDATE)
                    local_weather.full_update_enabled = False

                self.epd.displayPartial(self.epd.getbuffer(image))

        except Exception as e:
            print('There was an error updating the screen.')
            input(e)