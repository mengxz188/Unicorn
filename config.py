#!/usr/bin/evn python
#coding:utf-8

import sys
from library import Singleton



class Config(object):
    __metaclass__=Singleton
    def __init__(self):
        file_name='HEX4.xml'
        try: 
            import xml.etree.cElementTree as ET
        except ImportError: 
            import xml.etree.ElementTree as ET   
        try: 
            tree = ET.parse(file_name)
            self._root = tree.getroot()
        except Exception, e: 
            print "Error:cannot parse file:",file_name
            sys.exit(1)
        self._type  = self._root.get('type')
        self._FC    = self._root.get('FlightController')
        self._cloud = [self.get_node(0,1),self.get_node(0,2),self.get_node(0,3)]
        self._AIL   = [self.get_node(1,1)-1,self.get_node(1,2),self.get_node(1,3),self.get_node(1,4),self.get_node(1,5)]
        self._ELE   = [self.get_node(2,1)-1,self.get_node(2,2),self.get_node(2,3),self.get_node(2,4),self.get_node(2,5)]
        self._THR   = [self.get_node(3,1)-1,self.get_node(3,2),self.get_node(3,3),self.get_node(3,4),self.get_node(3,5)]
        self._RUD   = [self.get_node(4,1)-1,self.get_node(4,2),self.get_node(4,3),self.get_node(4,4),self.get_node(4,5)]
        self._PIT   = [self.get_node(5,1)-1,self.get_node(5,2),self.get_node(5,3),self.get_node(5,4),self.get_node(5,5)]
        self._mode  = [self.get_node(6,1)-1,self.get_node(6,2)]
        self._MCU   = [self.get_node(7,1),self.get_node(7,2),self.get_node(7,3)]
        self._GPS   = [self.get_node(8,1),self.get_node(8,2),self.get_node(8,3)]
        self._Comp = [self.get_node(9,1),self.get_node(9,2),self.get_node(9,3)]
        self._Baro  = [self.get_node(10,1),self.get_node(10,2),self.get_node(10,3)]
        self._lidar = [self.get_node(11,1),self.get_node(11,2),self.get_node(11,3),self.get_node(11,4)]
    def isInt(self,x):
        try:
            return isinstance(int(x),int)
        except ValueError:
            return False
    def get_node(self,param1,param2):
        value=self._root[param1][param2].get('value')
        if self.isInt(value) is True:
            return int(value)
        else:
            return value
    def get_type(self):
        return self._type
    def get_FC(self):
        return self._FC
    def get_cloud(self):
        return self._cloud
    def get_AIL(self):
        return self._AIL
    def get_ELE(self):
        return self._ELE
    def get_THR(self):
        return self._THR
    def get_RUD(self):
        return self._RUD
    def get_mode(self):
        return self._mode
    def get_PIT(self):
        return self._PIT
    def get_MCU(self):
        return self._MCU
    def get_GPS(self):
        return self._GPS
    def get_compass(self):
        return self._Comp
    def get_Baro(self):
        return self._Baro
    def get_lidar(self):
        return self._lidar


# Global config
config=Config()

if __name__=="__main__":
    print config._type
    print config.get_cloud()
    print config.get_AIL()
    print config.get_ELE()
    print config.get_THR()
    print config.get_RUD()   
    print config.get_PIT()
    print config.get_mode()
    print config.get_MCU()
    print config.get_GPS()
    print config.get_compass()
    print config.get_Baro()
    print config.get_lidar()
