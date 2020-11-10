
#
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
import paho.mqtt.client as mqtt
import requests
import uuid
from apscheduler.schedulers.background import BackgroundScheduler
import config
import json
import logging
import time
from utils import HX711, Door_Controler, General_Reader
import cv2 as cv
import base64
import numpy as np
import os
import threading
import qrcode
import re
from PIL import Image, ImageDraw, ImageFont
#import screeninfo
#import gpiozero as gpio




#################### global communication format #######################
#
#  MQTT communication in format as follows:
#  {'id': machine_id, 'type': type, 'name': name, 'content': content}  
# param "id": machine_id, which should main machine and sub machine share same, but unique among nets.
# param "type": sensor name, like "smoke", "fire", "full".
# param "name": sensor name, like "bottle" or "Null" if no name given.
# param "content": sensor status, usually a list in content int of 0/1.
#
# human exist report share similar format whit MQTT format, but transfor through HTTP/HTTPS.
#
#  URAT communicaton used for two board, which format as follows:
#  {'class':class, 'type': type, 'name':name, 'param':param}
# param "class": define what this sentence do, such as "command", "summary", report.




class Reporter():
    def __init__(self,):
        time.sleep(2)
        self.enable_fire_report = config.enable_fire_report
        if self.enable_fire_report:
            self.fire_io = General_Reader(config.fire_pins)

        self.enable_smoke_report = config.enable_smoke_report
        if self.enable_smoke_report:
            self.smoke_io = General_Reader(config.smoke_pins)

        self.enable_human_report = config.enable_human_report
        if self.enable_human_report:
            self.human_io = General_Reader(config.human_pins)
            self.capturer = cv.VideoCapture(0)
            self.camera_resolution = config.camera_resolution
            '''
            self.camera = picamera.PiCamera()
            self.camera.resolution = self.camera_resolution
            self.camera.framerate = config.camera_framerate
            '''
            self.upload_url = config.image_upload_url
    
    def report_fire(self,):
        if self.enable_fire_report:
            fire_sta = self.fire_io.read()
            if 0 in fire_sta:
                logging.warning('fire '+str(fire_sta))
                self.send(type='fire', name='None', content=fire_sta)
            else:
                pass
        else:
            pass
    
    def report_smoke(self,):
        #logging.warning('smoke')
        if self.enable_smoke_report:
            smoke_sta = self.smoke_io.read()
            if 0 in smoke_sta:
                logging.warning('smoke '+str(smoke_sta))
                self.send(type='smoke', name='None', content=smoke_sta)
            else:
                pass
        else:
            pass
    
    def report_human(self,):
        #print(self.human_io.read())
        if self.enable_human_report and 1 in self.human_io.read():
            #logging.warning('call human')
            # functional error when using picamera lib, switch to opencv method
            '''
            image = np.empty((self.camera_resolution[1] * self.camera_resolution[0] * 3,), dtype=np.uint8)
            self.camera.capture(image, 'bgr')
            image = image.reshape((self.camera_resolution[1], self.camera_resolution[0], 3))
            
            '''
            ret, image = self.capturer.read()
            image = cv.resize(image, self.camera_resolution)
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            
            img_str = cv.imencode('.jpg', image)[1].tostring()
            b64_code = base64.b64encode(img_str)
            info = str({'id': machine_id, 'type': 'human', 'name': 'Null', 'content': b64_code})
            response = requests.post(self.upload_url, data = info)
            print(response.text)
        else:
            pass
    
    def send(self, type, name, content, qos=0, through_http = False):
        ################### something more
        global client
        info = json.dumps({'id': machine_id, 'type': type, 'name': name, 'content': content})
        client.publish(config.mqtt_pub_path, payload=info, qos=qos)
    
    def start(self,):
        global scheduler
        if self.enable_fire_report:
            scheduler.add_job(self.report_fire, 'interval', seconds=config.fire_report_duration)
        if self.enable_human_report:
            scheduler.add_job(self.report_human, 'interval', seconds=config.human_report_duration)
        if self.enable_smoke_report:
            scheduler.add_job(self.report_smoke, 'interval', seconds=config.smoke_report_duration)

class Play_adv():
    def __init__(self,):
        from config import adv_dir
        self.dir = adv_dir
        self.adv_list = os.listdir(self.dir)
        
    def play(self,):
        #screen = screeninfo.get_monitors()[0]
        cv.namedWindow('advertisement_screen', cv.WND_PROP_FULLSCREEN)
        #cv.moveWindow('advertisement_screen', screen.x - 1, screen.y - 1)
        cv.setWindowProperty('advertisement_screen', cv.WND_PROP_FULLSCREEN,cv.WINDOW_FULLSCREEN)
        in_frames = [cv.VideoCapture(self.dir+item) for item in self.adv_list]
        while True:
            for vid in in_frames:
                ret, frame = vid.read()
                cv.imshow('advertisement_screen',frame)
                cv.waitKey(30)
                
    def play_background(self):
        adv_thread = threading.Thread(target=self.play)
        adv_thread.start()

class Screen():
    def __init__(self,):
        
        self.background = cv.imread('./background.jpg')
        assert self.background.shape == (900,1600,3)
        self.qr_y = 200
        self.qr_x = 100
        self.qr_w = 500
        self.throw = cv.imread('./throw.jpg')
        self.box_name = config.all_box_name
        self.box_name_cn = config.all_box_name_cn
        self.qr_url = config.qr_url
        self.font = ImageFont.truetype('./black_simple.ttf', 20, encoding="utf-8")
        cv.namedWindow('1', cv.WINDOW_NORMAL)
        cv.setWindowProperty('1', cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
        global scheduler
        scheduler.add_job(self.extend_life, 'interval', seconds=2)
        
    def qr(self,):
        qr0 = qrcode.QRCode()
        qr0.add_data(self.qr_url+self.box_name[0]+';;'+machine_id+';;'+str(time.time()))
        qr0 = np.array(qr0.make_image().convert('RGB'))
        qr0 = cv.resize(qr0,(self.qr_w, self.qr_w))
        qr1 = qrcode.QRCode()
        qr1.add_data(self.qr_url+self.box_name[1]+';;'+machine_id+';;'+str(time.time()))
        qr1 = np.array(qr1.make_image().convert('RGB'))
        qr1 = cv.resize(qr1,(self.qr_w, self.qr_w))
        img = self.background.copy()
        img[self.qr_y:self.qr_y+self.qr_w, self.qr_x:self.qr_x+self.qr_w] = qr0
        img[self.qr_y:self.qr_y+self.qr_w, len(img[0])-self.qr_w-self.qr_x:len(img[0])-self.qr_x] = qr1
        
        pil_im = Image.fromarray(img)
        draw = ImageDraw.Draw(pil_im)
        draw.text((self.qr_x, self.qr_y+self.qr_x+500), self.box_name_cn[0], (0, 0, 255), font=self.font) 
        draw.text((len(img[0])-self.qr_w-self.qr_x, self.qr_y+self.qr_x+500), self.box_name_cn[1], (0, 0, 255), font=self.font) 
        img = np.array(pil_im)
        cv.imshow('1', img)
        cv.waitKey(100)
    
    def extend_life(self,):
        cv.waitKey(100)


class Card_Reader():
    def __init__(self,):
        from mfrc522 import SimpleMFRC522
        self.card_name = config.card_name
        self.reader = SimpleMFRC522()
        #self.card_url = config.card_request_url
    
    def read_and_request(self,):
        while True:
            icid, ickey = self.reader.read()
            print(ickey)
            print(icid)
            global client
            info = json.dumps({'id': machine_id, 'type': 'card', 'name': self.card_name, 'content': [icid, ickey]})
            client.publish(config.mqtt_pub_path, payload=info, qos=0)
            time.sleep(10)
        
    def start_read(self,):
        card_thread = threading.Thread(target=self.read_and_request, name='card_reader.read')
        card_thread.start()

class Throw():
    def __init__(self):
        from config import box
        #print('\n\nThrow init once \n\n')
        self.box_names = box['name']
        self.door = Door_Controler(box['moter_pins'], box['hand_pin'], box['wait_duration'], box['motor_runtime'], box['no_hand_back'])
        self.weight = HX711(box['weight_clock_pin'], box['weight_output_pin'], box['arrange'], box['k'], box['b'])
        self.fulls = General_Reader(box['full_pins'])
        
    def process(self,run_name):
        if run_name != self.box_names:
            return 0
        w0 = self.weight.read()
        self.door.run()
        w1 = self.weight.read()
        full_sta = self.fulls.read()
        cotnt = [w0,w1]
        cotnt.extend(full_sta)
        print(cotnt)
        event_summary = {'class':'summary','type':'door','name':self.box_names, 'content':cotnt}
        return event_summary


################## MQTT function ###############
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    #client.subscribe("command/"+machine_id)
    client.subscribe('command/#')

def on_message(client, userdata, msg):
    dt = json.loads(msg.payload.decode())
    print(dt)
    assert dt['machine_id'] == machine_id
    if dt['type'] == 'door':
        evevt_summary = throw.process(dt['name'])
        print(evevt_summary)
        if evevt_summary != 0:
            client.publish(config.mqtt_pub_path, payload=json.dumps(evevt_summary), qos=2)
    else:
        logging.warning('unrecognized type')

    
################################################

if __name__ == "__main__":
    machine_id = config.machine_id
    
    scheduler = BackgroundScheduler()
    
    mqtt_ip = config.mqtt_server_ip
    mqtt_port = config.mqtt_port
    
    
    if config.enable_screen_interface:
        screen = Screen()
        screen.qr()
        screen.extend_life()
        
    if config.enable_adv_play:
        adv = Play_adv()
        adv.play_background()
    
    carder  = Card_Reader()
    carder.start_read()
    
    client = mqtt.Client()
    client.connect(mqtt_ip, mqtt_port, 120)
    client.on_connect = on_connect
    client.on_message = on_message
    
    throw = Throw()
    
    reporter = Reporter()
    reporter.start()
    
    scheduler.start()
    
    print('hahahah')
    client.loop_forever()

