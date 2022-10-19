import logging
import time
from threading import Thread

from core.pi_pwm import PiPwm
from core.mqtt_connector import MqttConnector

FADE_STEPS = 60

MQTT_TOPIC_COLOR_SUFFIX = "color"
MQTT_TOPIC_POWER_SUFFIX = "power"
MQTT_TOPIC_BRIGHTNESS_SUFFIX = "brightness"


class ColorLightHandler:
    def __init__(self, mqtt_connector: MqttConnector, pwm: PiPwm, mqtt_basetopic: str,
                 id: str, channel_ids: (), value_range: int):
        self.__id = id
        self.__channel_ids = channel_ids
        self.__pwm = pwm
        self.__value_range = value_range

        self.__fade_thread = None
        self.__stop_thread_trigger = False

        self.__current_rgb_values = (0,) * len(channel_ids)
        self.__last_state_rgb_values = (0,) * len(channel_ids)
        self.__current_brightness = 0.0
        self.__last_state_brightness = 0.0
        self.__light_state_on = False

        logging.debug("Init LedStripLight with name %s", id)
        mqtt_connector.subscribe_to_topic(mqtt_basetopic + "/" + id + "/" + MQTT_TOPIC_POWER_SUFFIX,
                                          self.__handle_power_command)
        mqtt_connector.subscribe_to_topic(mqtt_basetopic + "/" + id + "/" + MQTT_TOPIC_COLOR_SUFFIX,
                                          self.__handle_color_command)
        mqtt_connector.subscribe_to_topic(mqtt_basetopic + "/" + id + "/" + MQTT_TOPIC_BRIGHTNESS_SUFFIX,
                                          self.__handle_brightness_command)

    def is_fading(self):
        return self.__fade_thread is not None and self.__fade_thread.is_alive()

    def is_on(self):
        return self.__light_state_on

    def fade_to_colors(self, rgb_state: (int, int, int), brightness: float):
        if self.is_fading():
            self.__stop_fading()

        logging.debug("Start fading for light '%s'...", self.__id)
        self.__stop_thread_trigger = False
        self.__fade_thread = Thread(target=self.__do_fade, args=(rgb_state, brightness, lambda: self.__stop_thread_trigger))
        self.__fade_thread.start()

    def get_current_rgb_values(self):
        return self.__current_rgb_values

    def get_channel_ids(self):
        return self.__channel_ids

    def __handle_power_command(self, message):
        light_state = str(message.decode("utf-8"))
        logging.debug("Handle power command for light '%s': %s", self.__id, light_state)

        if light_state == "ON":
            self.__light_state_on = True
            self.fade_to_colors(self.__last_state_rgb_values, self.__last_state_brightness)
        else:
            self.__light_state_on = False
            self.fade_to_colors(self.__last_state_rgb_values, 0.0)

    def __handle_color_command(self, message):
        color_state = str(message.decode("utf-8"))
        logging.debug("Handle color command for light %s: %s", self.__id, color_state)
        values = color_state.split(";")
        new_colors = ()

        for value in values:
            new_colors = new_colors + (int(float(value)),)

        self.__last_state_rgb_values = new_colors
        if self.__light_state_on:
            self.fade_to_colors(new_colors, self.__last_state_brightness)

    def __handle_brightness_command(self, message):
        brightness_state = str(message.decode("utf-8"))
        logging.debug("Handle brightness command for light %s: %s", self.__id, brightness_state)
        new_brightness = float(brightness_state / self.__value_range)

        self.__last_state_brightness = new_brightness
        if self.__light_state_on:
            self.fade_to_colors(self.__last_state_rgb_values, new_brightness)

    def __stop_fading(self):
        if self.is_fading():
            self.__stop_thread_trigger = True
            self.__fade_thread.join()
            logging.debug("Cancelled fading for light '%s'...", self.__id)

    def __do_fade(self, target_rgb_values: (), target_brightness: float, stop):
        initial = ()
        diff = ()
        for i in range(0, len(self.__current_rgb_values)):
            initial = initial + (self.__current_rgb_values[i],)
            target = target_rgb_values[i] / self.__value_range * 4095 * target_brightness
            diff = diff + (target - initial[i],)

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
