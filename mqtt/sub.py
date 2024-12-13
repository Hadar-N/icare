import os
import paho.mqtt.client as mqtt
# from consts import *
from dotenv import load_dotenv

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    # Be careful, the reason_code_list is only present in MQTTv5. In MQTTv3 it will always be empty
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
    else:
        print(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()

def on_message(client, userdata, message):
    # userdata.append(message.payload)
    print("internal on_message",message.payload)

def on_connect(TOPIC):
    def on_connect_inner(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
        else:
            # we should always subscribe from on_connect callback to be sure our subscribed is persisted across reconnections.
            client.subscribe(TOPIC)
    return on_connect_inner

def init_sub(external_on_message):
    load_dotenv(verbose=True, override=True)

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect(os.getenv("TOPIC"))
    mqttc.on_unsubscribe = on_unsubscribe
    mqttc.on_message = external_on_message

    mqttc.username_pw_set(username=os.getenv("USERNAME"),password=os.getenv("PASSWORD"))
    mqttc.connect(os.getenv("HOST"), int(os.getenv("PORT")))
    mqttc.loop_start()

    return mqttc

def on_close(mqtcc, TOPIC):
    mqtcc.disconnect()
    mqtcc.unsubscribe(TOPIC) # TODO: (tofix) goes to package unsubscribe instead on mqtt_sub on_unsubscribe
    mqtcc.loop_stop()
