import os
import paho.mqtt.client as mqtt
from logging import Logger
from dotenv import load_dotenv
from utils.consts import MQTT_TOPIC_CONTROL, MQTT_COMMANDS
from utils.gamePlay import GamePlay

class MQTTSubscribe:
    def __init__(self, logger: Logger, gamePlay: GamePlay):
        load_dotenv(verbose=True, override=True)
        self.__logger = logger
        self.__gamePlay = gamePlay
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(username=os.getenv("USERNAME"),password=os.getenv("PASSWORD"))
        self.client.connect(os.getenv("HOST"), int(os.getenv("PORT")))
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, props):
        self.__logger.info("Connected with result code "+str(rc))
        print("Connected with result code "+str(rc))
        client.subscribe(MQTT_TOPIC_CONTROL)

    def on_close(self):
        self.client.disconnect()
        self.client.loop_stop()

    def on_message(self, client, userdata, msg):
        print(f"Received control command:", msg)
        if msg.topic == MQTT_TOPIC_CONTROL:
            command = msg.payload.decode()
            self.handle_control_command(command)
        
    def handle_control_command(self, command):
        if command == MQTT_COMMANDS.START.value:
            # Start pygame game
            self.__gamePlay.startGame()
            pass
        elif command == MQTT_COMMANDS.PAUSE.value:
            # Pause game
            pass
        elif command == MQTT_COMMANDS.STOP.value:
            # Stop game
            pass
