#!/usr/bin/evn python
# coding:utf-8

import json
import time

from attribute import Attribute
from config import config
from library import (CancelWatcher, GCS_package, Singleton, Watcher, _angle,
                     angle_heading_target, get_distance_metres, list_assign,
                     radio_package)
from waypoint import Waypoint

hasMCU = False
if config.get_MCU()[
        0] > 0:                       # instancce of MCU module object
    hasMCU = True


class Vehicle(Attribute):
    __metaclass__ = Singleton

    def __init__(self, mcu=None, compass=None, GPS=None):
        super(Vehicle, self).__init__(mcu, compass, GPS)

    def GCS(self):
        self._log('Switch to GCS')
        self.mode_name = 'LOITER'
        if hasMCU:
            msg = GCS_package()
            self.mcu.send_msg(msg)

    def radio(self):
        self._log('Switch to Radio')
        self.mode_name = 'Radio'
        if hasMCU:
            msg = radio_package()
            self.mcu.send_msg(msg)

    def arm(self, duration=3):
        # self.home_location=self.get_location()
        # self.channels[self.THR[0]]=self.THR[1]
        # self.channels[self.RUD[0]]=self.RUD[3]
        # self.send_pwm()
        # time.sleep(duration)
        # self.channels[self.RUD[0]]=self.RUD[2]
        # self.send_pwm()
        pass

    def disarm(self, duration=3):
        # self.channels[self.THR[0]]=self.THR[1]
        # self.channels[self.RUD[0]]=self.RUD[1]
        # self.send_pwm()
        # time.sleep(duration)
        # self.channels[self.RUD[0]]=self.RUD[2]
        # self.send_pwm()
        pass

    def stall(self):
        self._log("stall")
        self.channels[self.THR[0]] = self.THR[1]
        if self.PIT[1] > 0:
            self.channels[self.PIT[0]] = self.PIT_curve(self.THR[1])
        self.send_pwm()

    def takeoff(self, alt=5):
        pass

    def movement(self, att, sign=1):
        rate = self.gear[self.get_gear()] / 100.0
        variation = int(att[5] * att[4] * rate)
        self.channels[att[0]] = att[2] + sign * variation
        return self.channels[att[0]]

    def movement2(self, att, sign=1):
        rate = att[6] / 100.0
        variation = int(att[5] * att[4] * rate)
        self.channels[att[0]] = att[2] + sign * variation
        return self.channels[att[0]]

    def yaw_left(self):
        self._log('Turn Left...')
        if hasMCU:
            self.movement2(self.RUD, -1)
            self.send_pwm()

    def yaw_right(self):
        self._log('Turn Right...')
        if hasMCU:
            self.movement2(self.RUD)
            self.send_pwm()

    def forward(self, duration=None):
        self._log('Forward...')
        if hasMCU:
            self.movement(self.ELE)
            self.send_pwm()
            if duration is not None:
                time.sleep(duration)
                self.brake()

    def brake(self):
        self._log('brake')
        if hasMCU:
            duration = self.BD[self.get_gear()]
            list_assign(self.channels, self.channels_mid)
            self.send_pwm()
            time.sleep(duration)

    def yaw_left_brake(self):
        duration = self.mDuration()
        self._log('Yaw Left')
        if hasMCU:
            self.movement2(self.RUD, -1)
            self.send_pwm()
            time.sleep(duration)
            self.brake()

    def yaw_right_brake(self):
        duration = self.mDuration()
        self._log('Yaw Right')
        if hasMCU:
            self.movement2(self.RUD)
            self.send_pwm()
            time.sleep(duration)
            self.brake()

    def forward_brake(self):
        duration = self.mDuration()
        self._log('Forward')
        if hasMCU:
            self.movement(self.ELE)
            self.send_pwm()
            time.sleep(duration)
            self.brake()

    def backward_brake(self):
        duration = self.mDuration()
        self._log('Backward')
        if hasMCU:
            self.movement(self.ELE, -1)
            self.send_pwm()
            time.sleep(duration)
            self.brake()

    def roll_left_brake(self):
        duration = self.mDuration()
        self._log('Roll Left')
        if hasMCU:
            self.movement(self.AIL, -1)
            self.send_pwm()
            time.sleep(duration)
            self.brake()

    def roll_right_brake(self):
        duration = self.mDuration()
        self._log('Roll Right')
        if hasMCU:
            self.movement(self.AIL)
            self.send_pwm()
            time.sleep(duration)
            self.brake()

    def up_brake(self):
        duration = self.mDuration()
        self._log('Throttle Up')
        if hasMCU:
            pwm = self.movement(self.THR)
            if self.PIT[1] > 0:
                self.channels[self.PIT[0]] = self.PIT_curve(pwm)
            self.send_pwm()
            time.sleep(duration)
            self.brake()

    def down_brake(self):
        duration = self.mDuration()
        self._log('Throttle Down')
        if hasMCU:
            pwm = self.movement(self.THR, -1)
            if self.PIT[1] > 0:
                self.channels[self.PIT[0]] = self.PIT_curve(pwm)
            self.send_pwm()
            time.sleep(duration)
            self.brake()

    def mDuration(self):
        return self.MD[0]

    def send_pwm(self):
        self.mcu.send_pwm(self.channels)

    def diff_angle(self, origin, target, sign):
        diff = (360 + sign * (target - origin)) % 360
        if diff < 180 and diff > 2:
            return True
        else:
            return False

    def condition_yaw(self, heading=0, relative=True):
        """
        0<=heading<360
        """
        if heading < 0 or heading >= 360:
            self._log('0<=heading<360')
            return -1
        if relative and heading == 0:
            return 0

        current_heading = self.get_heading()
        watcher = CancelWatcher()
        # Relative angle to heading
        if relative:
            target_angle = (current_heading + heading) % 360
        else:
            # Absolute angle
            target_angle = heading

        direction = (360 + target_angle - current_heading) % 360
        if direction > 0 and direction < 180:
            is_cw = 1
            self._log('Turn right {}'.format(direction))
            self.yaw_right()
        elif direction >= 180 and direction < 360:
            is_cw = -1
            self._log('Turn left {}'.format(360 - direction))
            self.yaw_left()

        while not watcher.IsCancel() and self.diff_angle(
                self.get_heading(), target_angle, is_cw):
            self._log(
                'Cur angle:{},Target angle:{}'.format(
                    self.get_heading(),
                    target_angle))
            time.sleep(.1)
        # self._log('Reached Angle {}'.format(self.get_heading()))
        self.brake()
        self._log('Reached Angle {}'.format(self.get_heading()))
        return 1

    def navigation(self, target):
        deviation = config.get_degree()[0]
        checktime = config.get_DD()[0]
        watcher = CancelWatcher()
        while not watcher.IsCancel():
            current_location = self.get_location()
            if current_location is None:
                self._log("GPS is Error")
                self.brake()
                break
            distance = round(get_distance_metres(current_location, target), 2)
            self._log("Distance to Target {}m".format(distance))
            if distance < 3:
                self._log("Reached Target Waypoint!")
                self.brake()
                break
            angle = angle_heading_target(
                current_location, target, self.get_heading())
            if _angle(angle) > deviation:
                self.brake()
                self.condition_yaw(angle)
            self.forward()
            time.sleep(checktime)

    def RTL(self):
        target = self.get_home()
        if target is None:
            self._log("Home is None!")
            self.brake()
            return -1
        self.mode_name = 'RTL'

        self.navigation(target)
        self.mode_name = "Loiter"

    def Auto(self):
        if self.wp == []:
            self._log('Waypoint is None')
            return -1
        self.mode_name = 'AUTO'
        watcher = CancelWatcher()
        for point in self.wp.remain_wp():
            if watcher.IsCancel():
                break
            self.navigation(point)
            self.wp.add_number()

        self.mode_name = "Loiter"
        self.wp.clear()

    def Guided(self):
        target = self.get_target()
        if target is None:
            self._log("Target is None!")
            self.brake()
            return -1
        self.mode_name = "GUIDED"

        self.navigation(target)
        self.mode_name = "Loiter"
        self.target = None

    def __str__(self):
        msg = {}
        msg['AIL'] = self.AIL
        msg['ELE'] = self.ELE
        msg['THR'] = self.THR
        msg['RUD'] = self.RUD
        msg['PIT'] = self.PIT
        msg['Mode'] = self.mode
        msg['Gear'] = self.gear
        msg['Target'] = self.target
        msg['Home'] = self.home_location
        msg['Mode_name'] = self.mode_name
        msg['Current_channels'] = self.channels
        msg['Loiter_channels'] = self.channels_mid
        msg['init_alt'] = self.init_alt
        return json.dumps(msg)

    def Cancel(self):
        self._log("Cancel")
        CancelWatcher.Cancel = True
        time.sleep(1)
        self.brake()

if __name__ == "__main__":
    Watcher()
    mcu = None
    gps = None
    compass = None
    if config.get_MCU()[
            0] > 0:                       # instancce of MCU module object
        from MCU_module import MCU
        mcu = MCU()

    vehicle = Vehicle(mcu, compass, gps)
    vehicle.radio()