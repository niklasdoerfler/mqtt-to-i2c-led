# mqtt-to-i2c-led

This project is intended to be used as a universal driver for different kind of lights and sensors around the Raspberry Pi.
The initial use case is controlling some led strips and pir sensors.

To realize the pwm signal generation, this project
makes use of an **Adafruit PCA9685** compatible servo driver board which is connected to the Pi via I²C bus.


## Requirements

- Raspberry Pi
- Adafruit PCA9685
- some kind of amplifier circuit (e. g. MOSFET or other LED driver)


## Installation

### Setup virtual environment

```bash
python3 -m venv venv
```

### Install dependencies

```bash
source venv/bin/activate
pip3 install -r requirements.txt
```

## Configuration

The program is designed to be configured via an .ini file with the following structure. 
The general section specifies the parameters to connect to your mqtt broker.
After that you can create multiple sections, each starting with `device:` in the section name, followed by an arbitrary name.
Each device section consists of the option `type`, which specifies if the device is a `color-light`, `on-off` device or a `pir`.

| `type`      | Description                                                                                     | Required options                                                                                                                              | Topics                                                 |
|-------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------|
| color-light | Represents a color light (e.g. a LED color strip), using three pwm channel (one foreach color). | - pins: defines the pwm channels <br />- id: name part of the mqtt topic <br />- basetopic: prefix part of the mqtt topic                     | - *{basetopic}*/*{id}*/power <br />- *{basetopic}*/*{id}*/color|
| on-off      | Represents a simple on/off switch, using one pwm channel.                                       | - pin: defines the pwm channel <br />- id: name part of the mqtt topic <br />- basetopic: prefix part of the mqtt topic                       | - *{basetopic}*/*{id}*/power                               |
| pir         | Represents a pir sensor, sending its state via mqtt message when it gets triggered.             | - gpio: defines the gpio pin connected to the sensor <br />- id: name part of the mqtt topic <br />- basetopic: prefix part of the mqtt topic | - *{basetopic}*/*{id}*/power                               |
```ini
[general]
mqtt_host: broker.youdomain.tld
mqtt_port: 1883
mqtt_protocol: tcp

[device:lamp1]
type: color-light
pins: 0, 1, 2
id: lamp1
base_topic: smarthome/lights

[device:lamp2]
type: on-off
pin: 6
id: lamp2
base_topic: smarthome/lights

[device:pir]
type: pir
gpio: 23
id: movement-room1
base_topic: smarthome/sensors

```

## Running

Run this manually with

```bash
venv/bin/python main.py
```

Or by using [attached systemd service template](mqtt-to-i2c-led.example.service). After setting the path to this program
and copying the `.service` file to `/etc/systemd/system/mqtt-to-i2c-led.service` you can start the service as follows:

```bash
systemctl start mqtt-to-i2c-led
```

To autostart the service on each system boot, enable it:

```bash
systemctl enable mqtt-to-i2c-led
```