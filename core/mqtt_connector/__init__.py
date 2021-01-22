import paho.mqtt.client as mqtt
import collections
import logging


class MqttConnector:

    def __init__(self, server, port, transport):
        self.__is_connected = False
        self.__topic_handlers = collections.defaultdict(set)
        self.__client = mqtt.Client(transport=transport)
        self.__client.on_connect = self.__on_connect
        self.__client.on_disconnect = self.__on_disconnect
        self.__client.on_message = self.__on_message
        if transport == 'websockets':
            self.__client.tls_set()
        self.__server = server
        self.__port = port
        self.__transport = transport
        self.__client.connect(server, port)
        self.__client.loop_start()

    def subscribe_to_topic(self, topic, callback):
        self.__topic_handlers[topic].add(callback)
        if self.__is_connected:
            self.__client.subscribe(topic)

    def publish(self, topic, payload=None, qos=0, retain=False):
        return self.__client.publish(topic, payload, qos, retain)

    def __on_connect(self, client, userdata, flags, rc):
        self.__is_connected = True
        logging.info("Connected to mqtt broker at %s:%d with result code %d", self.__server, self.__port, rc)
        self.__resubscribe_to_topics()

    def __resubscribe_to_topics(self):
        for topic in self.__topic_handlers.copy():
            logging.debug("Resubscribing to topic '%s'", topic)
            self.__client.subscribe(topic)

    def __on_disconnect(self, client, userdata, rc):
        self.__is_connected = False
        logging.warning("Disconnected with result code %d", rc)

    def __on_message(self, client, userdata, msg):
        self.__trigger_handler_callbacks(msg.topic, msg.payload)

    def __trigger_handler_callbacks(self, topic, payload):
        if topic in self.__topic_handlers:
            for handler in self.__topic_handlers.get(topic, []):
                handler(payload)
