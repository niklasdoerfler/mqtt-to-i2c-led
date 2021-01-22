import logging
from threading import Lock

import Adafruit_PCA9685


class PiPwm:
    __pwm = Adafruit_PCA9685.PCA9685()
    __pwm.set_pwm_freq(1000)

    __lock = Lock()

    CHANNEL_RANGE_START = 0
    CHANNEL_RANGE_END = 15

    CHANNEL_VALUE_MIN = 0
    CHANNEL_VALUE_MAX = 4095

    def __init__(self):
        logging.debug("PiPwm created")

    def set_pwm_channel_value(self, pwm_channel_id: int, pwm_channel_value: int):
        self.__set_pwm_value(pwm_channel_id, pwm_channel_value)

    def set_pwm_channel_bool(self, pwm_channel_id: int, pwm_channel_active: bool):
        if pwm_channel_active is True:
            self.__set_pwm_value(pwm_channel_id, 4095)
        else:
            self.__set_pwm_value(pwm_channel_id, 0)

    def __set_pwm_value(self, pwm_channel_id: int, pwm_channel_value: int):
        if pwm_channel_id < self.CHANNEL_RANGE_START or pwm_channel_id > self.CHANNEL_RANGE_END:
            raise IndexError("Channel id must be in range between " + str(self.CHANNEL_RANGE_START) + " and " + str(
                self.CHANNEL_RANGE_END) + ".")

        if pwm_channel_value < self.CHANNEL_VALUE_MIN or pwm_channel_value > self.CHANNEL_VALUE_MAX:
            raise IndexError("Channel value must be in range between " + str(self.CHANNEL_VALUE_MIN) + " and " + str(
                self.CHANNEL_VALUE_MAX) + ".")

        with self.__lock:
            self.__pwm.set_pwm(pwm_channel_id, 0, int(pwm_channel_value))
