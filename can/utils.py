
import time
import logging
import matplotlib.pyplot as plt
import threading
import json
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

class HX711():
    # clock_pin refers to 'SCK' pin
    # out_pin refers to 'DT' pin
    # ranges: int of the capability with units grams
    def __init__(self, clock_pin, out_pin, ranges, k, b):
        self.clock = clock_pin
        self.digital_out = out_pin
        GPIO.setup(self.clock, GPIO.OUT)
        GPIO.output(self.clock, GPIO.LOW)
        GPIO.setup(self.digital_out, GPIO.IN)
        self.ranges = ranges
        self.k = k
        self.b = b

    def get_once(self,):
        GPIO.output(self.clock, GPIO.HIGH)
        #t0 = time.time_ns()
        ix = GPIO.input(self.digital_out)
        #t1 = time.time_ns()
        GPIO.output(self.clock, GPIO.LOW)
        #t2 = time.time_ns()
        #print((t1-t0)/1000., (t2-t1)/1000.)
        return ix

    def read_raw(self,):
        binary = [self.get_once() for _ in range(25)]
        raw = int(''.join(str(v) for v in binary[:-1]), 2)
        return raw

    def read(self,):
        raw = self.read_raw()
        weight = (raw*self.k + self.b)*self.ranges
        return weight


class Door_Controler():
    def __init__(self, moterpins, hand, during, moter_runtime, no_hand_waiting):
        setting = [GPIO.setup(pi, GPIO.OUT) for pi in moterpins]
        self.turn = lambda per: [GPIO.output(pi,va) for pi,va in zip(moterpins, per)]
        #self.step = lambda ios, pins: [(pin.on() if io == 1 else pin.off()) for io, pin in zip(ios, pins)]
        # what an amazing lambda func!!!!!  but abandond
        # self.step_pin = lambda io, pin: pin.on() if io == 1 else pin.off()
        # self.step = lambda ios, ids: self.step_pin(io, i) for io, i in zip(ios, ids)
        self.during = [during[0]-no_hand_waiting, during[1]-no_hand_waiting] #list [min_waitimg, max_waiting]
        self.hand = hand
        GPIO.setup(self.hand, GPIO.IN)
        
        
        self.base_interval = 0.001
        self.moter_runtime = moter_runtime # list [forwardtime, backwaerdtime]
        self.run_to = [[1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1], [1, 0, 0, 0]]
        self.reversed_run_to = self.run_to[::-1]
        self.detect_interval = 0.2
        self.count0 = int(no_hand_waiting//self.detect_interval)
        self.count1 = int(self.during[1]//self.detect_interval)

    def run(self):
        time.sleep(self.during[0])
        temp = []
        
        #open door
        for t in self.run_to*int(self.moter_runtime[0]//self.base_interval//8):
            self.turn(t)
            time.sleep(self.base_interval)
        self.turn([0,0,0,0]) # power off motor
        # wait throw
        while len(temp)<self.count0 or (temp[:self.count0]!=[0]*self.count0 and len(temp)<self.count1):
            time.sleep(self.detect_interval)
            temp.append(GPIO.input(self.hand))
            print(temp)
        
        #close door
        for t in range(int(self.moter_runtime[1]//self.base_interval//40)):
            for po in self.reversed_run_to*5:
                self.turn(po)
                time.sleep(self.base_interval)
            if GPIO.input(self.hand):
                time.sleep(1)
        
        self.turn([0,0,0,0]) # power off motor


class General_Reader():
    def __init__(self, re_pins):
        pin_io_setup = [GPIO.setup(pi, GPIO.IN) for pi in re_pins]
        self.re_pins = re_pins

    def read(self,):
        result = [GPIO.input(io) for io in self.re_pins]
        return result

'''
d0 = Door_Controler([6, 13, 19, 26], 4, [5,10], [5,5], 5)
d0.run()
'''

'''
if __name__ == "__main__":
    with open('./config.json', 'r') as f:
        config = json.load(f)
    #print(config)
    weight = {}
    door = {}
    
    for wei in config['weight']:
        weight[wei['name']] = hx711(wei['clock_pin'], wei['output_pin'], wei['arrange'],wei['k'],wei['b'])
    
    for dor in config['door']:
        door[dor['name']] = door_controler(dor['pins'], dor['hand'], dor['full'])
    
    cho = input('Test function:\n1.Test weight module\n2.Test door function\n3.Test camera function\n4.Watch sensor data')
    if cho == '1':
        while True:
            res = [weight[ix].read() for ix in weight.keys()]
            print(res)
            time.sleep(0.5)
    elif cho == '2':
        while True:
            res = [door[ix].running for ix in door.keys()]
            d0 = res[0]
            #d1 = res[1]
            #print(res)
            t1 = threading.Thread(target=d0,args=(10,))
            #t2 = threading.Thread(target=d1,args=(10,))
            t1.start()
            #t2.start()
            time.sleep(12)
    else:
        pass
'''
