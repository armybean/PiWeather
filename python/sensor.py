#!/usr/bin/python
# coding=utf-8

import ConfigParser
import logging
import os
import pprint
import sys
import time

import Adafruit_DHT
import MySQLdb


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

host = settings.get('Database', 'Host')
user = settings.get('Database', 'User')
password = settings.get('Database', 'Password')
database = settings.get('Database', 'Database')

sensor = Adafruit_DHT.DHT22
sensorPin = settings.get('Sensor', 'Pin')

# initialize temperatures
humidity = 0.0
temperature = 0.0

# status variables
lastInsert = 0
lastTemp = None
retries = 0

logging.basicConfig(filename=path + '/log_sensor.log', level=logging.DEBUG)

con = MySQLdb.connect(host, user, password, database)


# ------------------------------------------------- #
# Main                                              #
# ------------------------------------------------- #

try:
    while 1:
        humidity, temperature = Adafruit_DHT.read_retry(sensor, sensorPin)

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

            # write data to file
            f = open(path + '/sensor.dat', 'w+')
            f.write(str(temperature) + ':' + str(humidity))
            f.close()

            # only insert every 5 minutes to the DB
            if lastInsert < time.time() - 300:
                with con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO temperatures (sensor, date, temperature, humidity) VALUES (1, %s, %s, %s)",
                                (time.strftime('%Y-%m-%d %H:%M:%S'), "{: f}".format(temperature),
                                 "{: f}".format(humidity)))
                lastInsert = time.time()

        time.sleep(15)

except:
    logging.info(time.strftime("%d.%m.%Y %H:%M"))
    logging.debug(pprint.pprint(temperature))
    logging.debug(pprint.pprint(humidity))
    raise
