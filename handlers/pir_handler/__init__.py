import logging
import time
from threading import Thread

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO! This is probably because you need superuser privileges. You can achieve this "
          "by using 'sudo' to run your script")

from core.mqtt_connector import MqttConnector

MQTT_TOPIC_POWER_SUFFIX = "power"
MQTT_MESSAGE_ON = "ON"
MQTT_MESSAGE_OFF = "OFF"


class PirHandler:
    def __init__(self, mqtt_connector: MqttConnector, mqtt_basetopic: str, id: str, pin: int):
        self.__pin = pin
        self.__id = id
        self.__topic = mqtt_basetopic + "/" + id
        self.__mqtt_connector = mqtt_connector
        self.__pir_last_state = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN)

        self.__worker_thread = Thread(target=self.__polling_worker)
        self.__worker_thread.start()

        logging.debug("Init PirHandler with name %s", id)

    def __polling_worker(self):
        while True:
            if GPIO.input(self.__pin):
                pir_state = True
            else:
                pir_state = False

            if pir_state != self.__pir_last_state:
                state = MQTT_MESSAGE_ON if pir_state else MQTT_MESSAGE_OFF
                self.__mqtt_connector.publish(self.__topic, state)
                logging.debug("PIR status '%s' changed to: %s", self.__id, state)

            self.__pir_last_state = pir_state
            time.sleep(1)
