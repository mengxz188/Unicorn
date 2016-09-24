#!/usr/bin/evn python
#coding:utf-8

import serial,time
from library import open_serial,encode_hex
from config import config
from library import Singleton

class Compass(object):
    __metaclass__=Singleton
    def __init__(self):
        print "Connecting to Compass Module"
        con=config.get_compass()       
        self.ser = open_serial(con[1],con[2])

    def get_heading(self):
        command='6804000307'   
        package=self.compass_info(command,8)
        heading=self.decode_BCD(package[8:14])
        return int(heading)
    def get_pitch(self):
        command='6804000105'   
        package=self.compass_info(command,8)
        pitch=self.decode_BCD(package[8:14])
        return pitch
    def get_roll(self):
        command='6804000206'
        package=self.compass_info(command,8)
        roll=self.decode_BCD(package[8:14])
        return roll
    def get_attitude(self):
        command='6804000408'
        package=self.compass_info(command,28)
        pitch=self.decode_BCD(package[8:14])
        yaw=self.decode_BCD(package[14:20])
        roll=self.decode_BCD(package[20:26])
        return [pitch,yaw,roll]
    def compass_info(self,command,size=8):  
        command=command.decode("hex")
        n=self.ser.write(command)
        res=self.ser.read(size)
        package=encode_hex(res)
        print package
        return package

    def decode_BCD(self,package):
        sign=package[0]
        data=int(package[1:])/100.0
        if sign=='1':
            data=-data
        return data

    def close(self):
        if self.ser.is_open is True:
            self.ser.close()
# Global compass
compass=Compass()

if __name__=='__main__':
    
    print compass.get_pitch()
    print compass.get_roll()
    print compass.get_heading()
    print compass.get_attitude()