def Get_Display(screen):

    if screen == "epd2in13_V2":
        print(screen)
        from epd import epd2in13_V2
        return epd2in13_V2.Display()

    if screen == "epd2in13bc":
        print(screen)
        from epd import epd2in13bc
        return epd2in13bc.Display()