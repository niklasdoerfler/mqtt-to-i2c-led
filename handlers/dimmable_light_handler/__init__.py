import logging
import time
from threading import Thread

from core.pi_pwm import PiPwm
from core.mqtt_connector import MqttConnector

FADE_STEPS = 60

MQTT_TOPIC_BRIGHTNESS_SUFFIX = "brightness"
MQTT_TOPIC_POWER_SUFFIX = "power"


class DimmableLightHandler:
    def __init__(self, mqtt_connector: MqttConnector, pwm: PiPwm, mqtt_basetopic: str,
                 id: str, channel_id: int, value_range: int):
        self.__id = id
        self.__channel_ids = (channel_id,)
        self.__pwm = pwm
        self.__value_range = value_range

        self.__fade_thread = None
        self.__stop_thread_trigger = False

        self.__current_rgb_values = (0,) * len(self.__channel_ids)
        self.__last_state_rgb_values = (0,) * len(self.__channel_ids)
        self.__light_state_on = False

        logging.debug("Init DimmableLight with name %s", id)
        mqtt_connector.subscribe_to_topic(mqtt_basetopic + "/" + id + "/" + MQTT_TOPIC_POWER_SUFFIX,
                                          self.__handle_power_command)
        mqtt_connector.subscribe_to_topic(mqtt_basetopic + "/" + id + "/" + MQTT_TOPIC_BRIGHTNESS_SUFFIX,
                                          self.__handle_brightness_command)

    def is_fading(self):
        return self.__fade_thread is not None and self.__fade_thread.is_alive()

    def is_on(self):
        return self.__light_state_on

    def fade_to_brightness(self, brightness: int):
        if self.is_fading():
            self.__stop_fading()

        logging.debug("Start fading for light '%s'...", self.__id)
        self.__stop_thread_trigger = False
        self.__fade_thread = Thread(target=self.__do_fade, args=((brightness,) * len(self.__channel_ids), lambda: self.__stop_thread_trigger))
        self.__fade_thread.start()

    def get_current_brightness(self):
        return self.__current_rgb_values[0]

    def get_channel_id(self):
        return self.__channel_ids[0]

    def __handle_power_command(self, message):
        light_state = str(message.decode("utf-8"))
        logging.debug("Handle power command for light '%s': %s", self.__id, light_state)

        if light_state == "ON":
            self.__light_state_on = True
            self.fade_to_brightness(self.__last_state_rgb_values[0])
        else:
            self.__light_state_on = False
            self.fade_to_brightness(0)

    def __handle_brightness_command(self, message):
        msg = str(message.decode("utf-8"))
        logging.debug("Handle color command for light %s: %s", self.__id, msg)
        value = int(msg)
        self.__last_state_rgb_values = (value,)
        if self.__light_state_on:
            self.fade_to_brightness(value)

    def __stop_fading(self):
        if self.is_fading():
            self.__stop_thread_trigger = True
            self.__fade_thread.join()
            logging.debug("Cancelled fading for light '%s'...", self.__id)

    def __do_fade(self, target_rgb_values: (), stop):
        initial = ()
        diff = ()
        for i in range(0, len(self.__current_rgb_values)):
            initial = initial + (self.__current_rgb_values[i],)
            target = target_rgb_values[i] / self.__value_range * 4095
            diff = diff + ((target - initial[i]),)

        for step in range(0, FADE_STEPS):
            current = ()
            for i in range(0, len(self.__current_rgb_values)):
                value = int(initial[i] + (step + 1) * (diff[i] / FADE_STEPS))
                current = current + (value,)
                self.__pwm.set_pwm_channel_value(self.__channel_ids[i], value)
            self.__current_rgb_values = current

            if stop():
                break

            time.sleep(0.005)
        logging.debug("Finished fading for light '%s'...", self.__id)
