from flask import Flask, render_template, request, send_from_directory
import os
import threading
import time
import paho.mqtt.client as mqtt
import json

# This is the Subscriber

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("report/#")

def on_message(client, userdata, msg):
    print(userdata)
    igs = json.loads(msg.payload.decode())
    print(igs)
    if igs['type'] == 'card':
        machine = igs['id']
        tong = igs['name']
        co = json.dumps({'machine_id':machine, 'type':'door', 'name':tong})
        client.publish('command/'+machine+'/', payload=co)

app = Flask(__name__)

@app.route('/test', methods=['GET','POST'])
def test():
    print(request.get_data().decode('utf-8'))
    return 'True',200

@app.route('/human', methods=['POST'])
def receive_human():
    print('get human image')
    return 'huamn_yes', 200


@app.route('/qr/<ifo>', methods=['GET'])
def qr(ifo):
    ifo = ifo.split(';;')
    print(ifo)
    tong = ifo[0]
    machine = ifo[1]
    co = json.dumps({'machine_id':machine, 'type':'door', 'name':tong})
    client.publish('command/'+machine+'/', payload=co)
    return 'yes', 200

if __name__ == "__main__":
    client = mqtt.Client()
    client.connect("127.0.0.1",1883,60)
    client.on_connect = on_connect
    client.on_message = on_message
    t0 = threading.Thread(target=client.loop_forever)
    t0.start()

    app.run('0.0.0.0',80,debug=True)
