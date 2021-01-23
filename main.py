#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import logging

from configparser import ConfigParser
from ast import literal_eval
from core.mqtt_connector import MqttConnector
from core.pi_pwm import PiPwm

from handlers.color_light_handler import ColorLightHandler
from handlers.dimmable_light_handler import DimmableLightHandler
from handlers.on_off_handler import OnOffHandler
from handlers.pir_handler import PirHandler

CONFIG_FILENAME = 'config.ini'

SECTION_GENERAL = "general"

OPTION_TYPE = "type"
DEVICE_TYPE_PIR = "pir"
DEVICE_TYPE_ON_OFF = "on-off"
DEVICE_TYPE_COLOR_LIGHT = "color-light"
DEVICE_TYPE_DIMMABLE_LIGHT = "dimmable-light"
OPTION_BASE_TOPIC = "base_topic"

OPTION_MQTT_PROTOCOL = "mqtt_protocol"
OPTION_PIN = "pin"
OPTION_PINS = "pins"
OPTION_ID = "id"
OPTION_VALUE_RANGE = "value_range"
OPTION_MQTT_PORT = "mqtt_port"
OPTION_MQTT_HOST = "mqtt_host"

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logging.root.setLevel(logging.INFO)

mqtt_conn = None
pwm = None


def initialize():
    global mqtt_conn, pwm

    parser = ConfigParser()
    parser.read(CONFIG_FILENAME)

    mqtt_host = parser.get(SECTION_GENERAL, OPTION_MQTT_HOST)
    mqtt_port = parser.getint(SECTION_GENERAL, OPTION_MQTT_PORT)
    mqtt_protocol = parser.get(SECTION_GENERAL, OPTION_MQTT_PROTOCOL)

    mqtt_conn = MqttConnector(mqtt_host, mqtt_port, mqtt_protocol)
    pwm = PiPwm()

    for section_name in parser.sections():
        device_match = re.search('device:(.*)', section_name, re.IGNORECASE)
        if device_match:
            device_name = device_match.group(1)
            device_type = parser.get(section_name, OPTION_TYPE, fallback=None)

            if device_type == DEVICE_TYPE_COLOR_LIGHT:
                device_id = parser.get(section_name, OPTION_ID, fallback=None)
                device_pins = literal_eval(parser.get(section_name, OPTION_PINS, fallback=None))
                device_base_topic = parser.get(section_name, OPTION_BASE_TOPIC, fallback=None)
                device_value_range = parser.getint(section_name, OPTION_VALUE_RANGE, fallback=None)

                ColorLightHandler(mqtt_conn, pwm, mqtt_basetopic=device_base_topic,
                                  id=device_id, channel_ids=device_pins, value_range=device_value_range)
                logging.info(
                    "Created color-light device: '{}', pins: {}, topic: {}, id: {}".format(device_name, device_pins,
                                                                                           device_base_topic,
                                                                                           device_id))

            if device_type == DEVICE_TYPE_DIMMABLE_LIGHT:
                device_id = parser.get(section_name, OPTION_ID, fallback=None)
                device_pin = parser.getint(section_name, OPTION_PIN, fallback=None)
                device_base_topic = parser.get(section_name, OPTION_BASE_TOPIC, fallback=None)
                device_value_range = parser.getint(section_name, OPTION_VALUE_RANGE, fallback=None)

                DimmableLightHandler(mqtt_conn, pwm, mqtt_basetopic=device_base_topic,
                                     id=device_id, channel_id=device_pin, value_range=device_value_range)
                logging.info(
                    "Created dimmable-light device: '{}', pin: {}, topic: {}, id: {}".format(device_name, device_pin,
                                                                                             device_base_topic,
                                                                                             device_id))

            if device_type == DEVICE_TYPE_ON_OFF:
                device_id = parser.get(section_name, OPTION_ID, fallback=None)
                device_pin = parser.getint(section_name, OPTION_PIN, fallback=None)
                device_base_topic = parser.get(section_name, OPTION_BASE_TOPIC, fallback=None)

                OnOffHandler(mqtt_conn, pwm, mqtt_basetopic=device_base_topic, id=device_id, channel_id=device_pin)
                logging.info("Created on-off device: '{}', pins: {}, topic: {}, id: {}".format(device_name, device_pin,
                                                                                               device_base_topic,
                                                                                               device_id))

            if device_type == DEVICE_TYPE_PIR:
                device_id = parser.get(section_name, OPTION_ID, fallback=None)
                device_pin = parser.getint(section_name, "gpio", fallback=None)
                device_base_topic = parser.get(section_name, OPTION_BASE_TOPIC, fallback=None)

                PirHandler(mqtt_conn, mqtt_basetopic=device_base_topic, id=device_id, pin=device_pin)
                logging.info("Created pir device: '{}', gpio: {}, topic: {}, id: {}".format(device_name, device_pin,
                                                                                            device_base_topic,
                                                                                            device_id))


if __name__ == "__main__":
    initialize()

    while True:
        time.sleep(2)
