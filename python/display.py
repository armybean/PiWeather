#!/usr/bin/python
# coding=utf-8

import ConfigParser
import logging
import MySQLdb as mdb
import os
import pprint
import RPi.GPIO as GPIO
import sys
import time

import Adafruit_DHT
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

import Image
import ImageDraw
import ImageFont


# ------------------------------------------------- #
# Configuration                                     #
# ------------------------------------------------- #

RESET_PIN = 17
SENSOR_PIN = 18
RST = 24
DC = 23

SPI_PORT = 0
SPI_DEVICE = 0

padding = 2  # Padding on the display

sensor = Adafruit_DHT.DHT22
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

# ------------------------------------------------- #
# Initialization                                    #
# ------------------------------------------------- #

# read config file
configFile = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'

if not os.path.isfile(configFile):
    print "No configuration file found."
    print "Please rename sample_config.ini to config.ini and edit the value to fit your setup."
    sys.exit()

settings = ConfigParser.ConfigParser()
settings.read(configFile)

DB_HOST = settings.get('Database', 'Host')
DB_USER = settings.get('Database', 'User')
DB_PASSWORD = settings.get('Database', 'Password')
DB_DATABASE = settings.get('Database', 'Database')

# Setup GPIO Pin for reset button
GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Initialize Display
disp.begin()
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

draw = ImageDraw.Draw(image)

# initialize temperatures
humidity = 0.0
temperature = 0.0

minTemp = 9999.99
maxTemp = -9999.99

# status variables
lastTemp = None
lastInsert = 0
retries = 0

top = padding
left = padding

# Load default font.
font = ImageFont.load_default()

con = mdb.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE)
logging.basicConfig(filename='weatherstation.log', level=logging.DEBUG)

try:
    while 1:
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        humidity, temperature = Adafruit_DHT.read_retry(sensor, SENSOR_PIN)

        if temperature is not None and humidity is not None:

            if lastTemp is None:
                lastTemp = temperature

            # sometime there are misread values - ignore them, try again after 15 seconds for maximum 4 times
            if abs(lastTemp - temperature) > 5 and retries < 5:
                retries += 1
                time.sleep(15)
                continue

            # reset retries
            retries = 0

            # reset min and max temperatures if button pressed
            if GPIO.input(RESET_PIN):
                maxTemp = -9999.99
                minTemp = 9999.99

            # we have a new max temperature
            if temperature > maxTemp:
                maxTemp = temperature

            # we have a new min temperature
            if temperature < minTemp:
                minTemp = temperature

            # only insert every 5 minutes to the DB
            if lastInsert < time.time() - 300:
                with con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO temperatures (sensor, date, temperature, humidity) VALUES (1, %s, %s, %s)",
                                (time.strftime('%Y-%m-%d %H:%M:%S'), "{: f}".format(temperature),
                                 "{: f}".format(humidity)))
                lastInsert = time.time()

            # Write two lines of text.
            draw.text((left, top), time.strftime("%d.%m.%Y %H:%M"), font=font, fill=255)
            draw.text((left, top + 20), '{0:.1f} *C  {1:.1f} % LF'.format(temperature, humidity), font=font, fill=255)
            draw.text((left, top + 40), 'min: {:.1f} *C'.format(minTemp), font=font, fill=255)
            draw.text((left, top + 50), 'max: {:.1f} *C'.format(maxTemp), font=font, fill=255)

            # Display image.
            disp.image(image)
            disp.display()

        time.sleep(15)

except:
    logging.info(time.strftime("%d.%m.%Y %H:%M"))
    logging.debug(pprint.pprint(temperature))
    logging.debug(pprint.pprint(humidity))
    raise
