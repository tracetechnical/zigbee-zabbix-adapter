import collections
import json
import jsonpickle
import paho.mqtt.client as mqtt
from flask import Flask


class Device:
    name: str
    battery: int
    lqi: int
    available: bool
    data: dict

    def serialise(self):
        return json.dumps(self.__dict__)


app = Flask(__name__, )


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("zigbee2mqtt/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    sections = msg.topic.split("/")
    device = sections[1]
    payload = str(msg.payload, "utf-8")
    if device == "bridge":
        return
    if len(sections) > 2:
        subpath = sections[2]
    else:
        subpath = ""

    if device not in devices:
        status = Device()
    else:
        status = devices[device]

    status.name = device
    if "{" in payload and "}" in payload:
        opts = json.loads(payload)
        keys = opts.keys()
        if "linkquality" in keys:
            status.lqi = opts["linkquality"]
        if "battery" in keys:
            status.battery = opts["battery"]
        else:
            if "battery_low" in keys:
                if not opts["battery_low"]:
                    status.battery = 100
                else:
                    status.battery = 10
        if subpath == "availability":
            status.available = opts["state"] == "online"
        status.data = opts
    devices[device] = status


@app.get("/")
def read_root():
    sorted_op = dict(sorted(devices.items()))
    list = []
    for item in sorted_op.values():
        list.append(item)
    return jsonpickle.encode(list, unpicklable=False, keys=False)


devices = {}

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("mqtt.io.home", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_start()
