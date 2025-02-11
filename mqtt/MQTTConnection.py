import os
import json
import paho.mqtt.client as mqtt
from logging import Logger
from dotenv import load_dotenv
from utils.consts import MQTT_TOPIC_CONTROL, MQTT_TOPIC_DATA
from utils.eventBus import EventBus

class MQTTConnection:

    def __init__(self, logger: Logger, eventbus: EventBus):
        load_dotenv(verbose=True, override=True)
        self.__logger = logger
        self.__eventbus = eventbus
        self.__eventbus.subscribe(MQTT_TOPIC_DATA, self.__publish_message)

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message

        try:
            self.client.username_pw_set(username=os.getenv("USERNAME"),password=os.getenv("PASSWORD"))
            self.client.connect(os.getenv("HOST"), int(os.getenv("PORT")))
            self.client.loop_start()
        except Exception as e:
            print("mqtt connection failed! error: ", e)

    def on_connect(self, client, userdata, flags, rc, props):
        self.__logger.info("Connected with result code "+str(rc))
        print("Connected with result code "+str(rc))
        client.subscribe(MQTT_TOPIC_CONTROL)

    def on_close(self):
        self.client.disconnect()
        self.client.loop_stop()

    def on_message(self, client, userdata, msg):
        if msg.topic == MQTT_TOPIC_CONTROL:
            command = msg.payload.decode()
            self.__eventbus.publish(MQTT_TOPIC_CONTROL, command)

    def on_publish(self, client, userdata, mid, reason_code, properties):
        try:
            self.__logger.info('message published status: '+ str(reason_code))
            # TODO: handle publish errors
        except KeyError:
            print(KeyError)


    def __publish_message(self, msg: list[object], topic = MQTT_TOPIC_DATA):
        msg_final =json.dumps(msg)
        self.__logger.info(f'publishing message: {msg_final} in topic: {topic}')
        msg_info = self.client.publish(topic, msg_final)
        msg_info.wait_for_publish()
