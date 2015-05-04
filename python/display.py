#!/usr/bin/python
#  -*- coding: utf-8 -*-

import time
import MySQLdb as mdb
import sys
import logging
import pprint

import Adafruit_DHT
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

import Image
import ImageDraw
import ImageFont


# Raspberry Pi pin configuration:
RST = 24
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

sensor = Adafruit_DHT.DHT22
pin = 18

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# initialize temperatures
humidity = 0.0
temperature = 0.0

minTemp = 9999
maxTemp = -9999

# status variables
lastTemp = None
lastInsert = 0
retries = 0

padding = 2
top = padding
x = padding

# Load default font.
font = ImageFont.load_default()

con = mdb.connect('localhost', 'weather', 'PASSWORD', 'weather')
logging.basicConfig(filename='weatherstation.log', level=logging.DEBUG)

try:
    while 1:
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

        if temperature is not None and humidity is not None:

            if lastTemp is None:
                lastTemp = temperature

            # sometime there are misread values - ignore them, try again after 15 seconds for maximum 4 times
            if abs(lastTemp - temperature) > 10 and retries < 5:
                retries += 1
                time.sleep(15)
                continue

            # reset retries
            retries = 0

            # we have a new max temperature
            if temperature > maxTemp:
                maxTemp = temperature

            # we have a new min temperature
            if temperature < minTemp:
                minTemp = temperature

            # only insert every 60 seconds to the DB
            if lastInsert < time.time() - 60:
                with con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO temperatures (sensor, date, temperature, humidity) VALUES (1, %s, %s, %s)",
                                (time.strftime('%Y-%m-%d %H:%M:%S'), "{: f}".format(temperature),
                                 "{: f}".format(humidity)))
                lastInsert = time.time()

            # Write two lines of text.
            draw.text((x, top), time.strftime("%d.%m.%Y %H:%M"), font=font, fill=255)
            draw.text((x, top + 20), '{0:.1f} *C  {1:.1f} % LF'.format(temperature, humidity), font=font, fill=255)
            draw.text((x, top + 40), 'min: {:.1f} *C'.format(minTemp), font=font, fill=255)
            draw.text((x, top + 50), 'max: {:.1f} *C'.format(maxTemp), font=font, fill=255)

            # Display image.
            disp.image(image)
            disp.display()

        time.sleep(15)

except:
    logging.info(time.strftime("%d.%m.%Y %H:%M"))
    logging.debug(pprint.pprint(temperature))
    logging.debug(pprint.pprint(humidity))
    raise
