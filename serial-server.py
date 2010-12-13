#!/usr/bin/python
import SocketServer
import threading
import time
import serial
import json
import sys
import os

l = [x for x in os.listdir('/dev') if 'USB' in x]
if len(l)>1:
    print 'Available serial interfaces:'
    for i in xrange(len(l)):
        print '%d. %s' % (i,l[i])
    choice = int(raw_input('Pick some one:'))
    port = '/dev/'+l[i]
else:
    port = '/dev/'+l[0]

names={}
def load_names():
    global names
    with open('names','r') as s:
        for line in s:
            names.update({line.split(' ')[0]:' '.join(line.split(' ')[1:])[:-1]})
load_names()
def save_names():
    global names
    with open('names','w') as s:
        for i in names:
            s.write(i+' '+names[i].encode('utf-8')+'\n')
        
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

def init():
    global ser
    global port
    global error
    try:
        ser = serial.Serial(port,timeout=5)
    except serial.SerialException,e:
        print 'Can\'t initialize serial port'
        return False
    time.sleep(1)
    ser.setDTR(level=0)
    time.sleep(1)
    return True
init()
def write_to_serial(x):
    try:
        ser.write(x)
    except:
        if init():
            ser.write(x)
        else:
            print 'Fails ro write'
            return False
    return True

def read_from_serial():
    try:
        r=ser.read()
    except:
        if init():
            r=ser.read()
        else:
            raise serial.SerialException('Can\'t read from serial')
    return r

def clear_input():
    try:
        ser.flushInput()
    except:
        if init():
            ser.FlushInput()
        else:
            raise serial.SerialException('Cannot flush input')

def power_on(x):
    if x=='all':
        # power on all
        return write_to_serial(chr(1))
    else:
        # power on x
        return write_to_serial(chr(4)+chr(int(x)))

def power_off(x):
    if x=='all':
        # power off all
        return write_to_serial(chr(0))
    else:
        # power off x
        return write_to_serial(chr(5)+chr(int(x)))

def get_state_of_pin(x):
    try:
        #clear_input()
        pass
    except:
        print 'Cannot flush input.'
        raise serial.SerialException('Cannot flush input.')
    if x=='all':
        if not write_to_serial(chr(6)):
            print 'Cannot write to Serial.'
            raise serial.SerialException('Cannot write to Serial.')
        print 'waiting'
        time.sleep(0.3)
        r=ser.readline()[:-1]
        return r
    else:
        if not write_to_serial(chr(3)+chr(int(x))):
            print 'Cannot write to Serial.'
            raise serial.SerialException('Cannot write to Serial.')
        time.sleep(0.3)
        try:
            r=read_from_serial()
        except:
            print 'Cannot read from serial.'
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
            if power_on(obj['n']):
                result={'result':'ok'}
            else:
                result={'result':'error'}
        elif obj['action']=='power_off':
            if power_off(obj['n']):
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
