import logging

from core.pi_pwm import PiPwm
from core.mqtt_connector import MqttConnector

MQTT_TOPIC_POWER_SUFFIX = "power"


class OnOffHandler:
    def __init__(self, mqtt_connector: MqttConnector, pwm: PiPwm, mqtt_basetopic: str,
                 id: str, channel_id: int):
        self.__id = id
        self.__channel_id = channel_id
        self.__pwm = pwm

        self.__current_state_on = False

        logging.debug("Init OnOffHandler with name %s", id)
        mqtt_connector.subscribe_to_topic(mqtt_basetopic + "/" + id + "/" + MQTT_TOPIC_POWER_SUFFIX,
                                          self.__handle_power_command)

    def is_on(self):
        return self.__current_state_on

    def set_on(self, state_on: bool):
        self.__current_state_on = state_on
        self.__pwm.set_pwm_channel_bool(self.__channel_id, self.__current_state_on)
        logging.debug("Set state for channel id '%s' to: %s.", self.__id, "ON" if self.__current_state_on else "OFF")

    def get_channel_ids(self):
        return self.__channel_id

    def __handle_power_command(self, message):
        state_string = str(message.decode("utf-8"))
        logging.debug("Handle power command for channel id '%s': %s", self.__id, state_string)
        self.set_on(state_string == "ON")
