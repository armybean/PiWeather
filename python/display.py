#!/usr/bin/python
# coding=utf-8

import ConfigParser
import logging
import os
import pprint
import subprocess
import sys
import time

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import Image
import ImageDraw
import ImageFont
import RPi.GPIO as GPIO


# ------------------------------------------------- #
# Configuration                                     #
# ------------------------------------------------- #

RESET_PIN = 17
PADDING = 2  # Padding on the display


# ------------------------------------------------- #
# Initialization                                    #
# ------------------------------------------------- #

path = os.path.dirname(os.path.realpath(__file__))

# read config file
configFile = path + '/config.ini'

if not os.path.isfile(configFile):
    print "No configuration file found."
    print "Please rename sample_config.ini to config.ini and edit the value to fit your setup."
    sys.exit()

settings = ConfigParser.ConfigParser()
settings.read(configFile)

rst = int(settings.get('Display', 'RST'))
dc = int(settings.get('Display', 'DC'))
spiPort = int(settings.get('Display', 'SPI_PORT'))
spiDevice = int(settings.get('Display', 'SPI_DEVICE'))

disp = Adafruit_SSD1306.SSD1306_128_64(rst=rst, dc=dc, spi=SPI.SpiDev(spiPort, spiDevice, max_speed_hz=8000000))

# Setup GPIO Pin for reset button
GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
line = None

top = PADDING
left = PADDING

# Load default font.
font = ImageFont.load_default()

logging.basicConfig(filename=path + '/log_weatherstation.log', level=logging.DEBUG)

sensorFile = path + '/sensor.dat'

subprocess.Popen(['python', path + '/sensor.py'])

try:
    while 1:
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        if not os.path.isfile(sensorFile):
            draw.text((left, top), 'Frage Sensor ab...', font=font, fill=255)
            time.sleep(15)
            continue

        f = open(sensorFile, 'r')
        line = f.readline().replace('\n', '')

        if line is None or line == '':
            continue

        temperature, humidity = [float(value) for value in line.split(':')]
        f.close()

        if temperature is not None and humidity is not None:

            # reset min and max temperatures if button pressed
            if not GPIO.input(RESET_PIN):
                maxTemp = -9999.99
                minTemp = 9999.99

            # we have a new max temperature
            if temperature > maxTemp:
                maxTemp = temperature

            # we have a new min temperature
            if temperature < minTemp:
                minTemp = temperature

            # Write two lines of text.
            draw.text((left, top), time.strftime("%d.%m.%Y %H:%M"), font=font, fill=255)
            draw.text((left, top + 20), '{0:.1f} *C  {1:.1f} % LF'.format(temperature, humidity), font=font, fill=255)
            draw.text((left, top + 40), 'min: {:.1f} *C'.format(minTemp), font=font, fill=255)
            draw.text((left, top + 50), 'max: {:.1f} *C'.format(maxTemp), font=font, fill=255)

            # Display image.
            disp.image(image)
            disp.display()

        time.sleep(.1)

except:
    logging.info(time.strftime("%d.%m.%Y %H:%M"))
    logging.debug(pprint.pprint(line))
    logging.debug(pprint.pprint(temperature))
    logging.debug(pprint.pprint(humidity))
    raise
