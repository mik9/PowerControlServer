#!/usr/bin/python
import SocketServer
import threading
import time
import serial
import json
import sys

names={}
def load_names():
    global names
    with open('names','r') as s:
        for line in s:
            names.update({line.split(' ')[0]:line.split(' ')[1][:-1]})
load_names()
def save_names():
    global names
    with open('names','w') as s:
        for i in names:
            s.write(i+' '+names[i]+'\n')
        
def get_name(x):
    global names
    x=str(x)
    if x in names:
        return names[x]
    else:
        return None
    
def set_name(x,name):
    x=str(x)
    names.update({x:name})
port='/dev/ttyUSB0'
def init():
    global ser
    global port
    global error
    try:
        ser = serial.Serial(port or '/dev/ttyUSB0',timeout=5)
    except serial.SerialException,e:
        error=e.message
        return False
    time.sleep(1)
    ser.setDTR(level=0)
    time.sleep(1)
    return True

def write_to_serial(x):
    try:
        ser.write(x)
    except:
        if init():
            ser.write(x)
            return True
        else:
            return False

def read_from_serial():
    try:
        r=ser.read()
        return r
    except:
        if init():
            r=ser.read()
            return r
        else:
            raise serial.SerialException('Can\'t read from serial')

def clear_input():
    try:
        ser.FlushInput()
    except:
        if init():
            ser.FlushInput()
        else:
            raise serial.SerialException('Cannot flush input')

def power_on_pin(x):
    return write_to_serial(chr(4)+chr(int(x)))

def power_off_pin(x):
    return write_to_serial(chr(5)+chr(int(x)))

def get_state_of_pin(x):
    try:
        clear_input()
    except:
        raise serial.SerialException('Cannot flush input.')
    if not write_to_serial(chr(3)+chr(x)):
        raise serial.SerialException('Cannot write to Serial.')
    time.sleep(0.3)
    try:
        r=read_from_serial()
    except:
        raise serial.SerialException('Cannot read from serial.')
    return r=='1'


class ThreadedTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024)
        cur_thread = threading.current_thread()
        try:
            obj = json.loads(str(self.data))
        except Exception,e:
            print e,': \''+self.data+'\''
            with open('q','w') as t:
                t.write(self.data)
            result={'result':'error'}
            self.request.send(json.dumps(result))
            return
        print 'request:',obj
        if obj['action']=='power_on':
            if power_on_pin(obj['n']):
                result={'result':'ok'}
            else:
                result={'result':'error'}
        elif obj['action']=='power_off':
            if power_off_pin(obj['n']):
                result={'result':'ok'}
            else:
                result={'result':'error'}
        elif obj['action']=='get_state':
            try:
                result={'result':'ok','state':get_state_of_pin(obj['n'])}
            except:
                result={'result':'error'}
        elif obj['action']=='get_name':
            result={'result':'ok','name':names[str(obj['n'])] if str(obj['n']) in names else "none"}
        elif obj['action']=='set_name':
            names.update({str(obj['n']):obj['name']})
            save_names()
            result={'result':'ok'}
        elif obj['action']=='reload_names':
            load_names()
            result={'result':'ok'}
        z=json.dumps(result)
        print 'response:',z,'\n'
        self.request.send(z)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

HOST, PORT = sys.argv[1] or 'localhost',int(sys.argv[2]) or 9000
print sys.argv
server = ThreadedTCPServer((HOST,PORT),ThreadedTCPHandler)
print server.server_address
#server_thread = threading.Thread(target=server.serve_forever)
#server_thread.setDaemon(True)
#server_thread.start()
server.serve_forever()
#print "Server loop running in thread:", server_thread.getName()
#time.sleep(100)