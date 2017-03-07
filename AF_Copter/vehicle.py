#!/usr/bin/evn python
# coding:utf-8

import sys
sys.path.append('..')
import time
import math
from attribute import Attribute
from AF_ML.Curve import THR2PIT
from lib.config import config
from lib.tools import CancelWatcher, Singleton
from lib.science import get_distance_metres, angle_heading_target, angle_diff
from lib.logger import logger


class Vehicle(Attribute):
    __metaclass__ = Singleton

    def __init__(self, ORB):
        super(Vehicle, self).__init__(ORB)
        self.moveTime = 2
        self.Epsilon = 20
        self.radius = 5
        self.frequence = 1
        self.prepre_state = 'STOP'
        self.pre_state = 'STOP'
        self._state = 'STOP'

    def brake(self, braketime=0.5):
        self.send_pwm(self.subscribe('LoiterPWM'))
        time.sleep(braketime)

    def control_stick(self, AIL=0, ELE=0, THR=0, RUD=0, Mode=2):
        channels = [0] * 8
        channels[self.AIL[0]] = self.AIL[2 + AIL * self.AIL[5]]
        channels[self.ELE[0]] = self.ELE[2 + ELE * self.ELE[5]]
        channels[self.THR[0]] = self.THR[2 + THR * self.THR[5]]
        channels[self.RUD[0]] = self.RUD[2 + RUD * self.RUD[5]]
        channels[self.mode[0]] = self.mode[Mode]
        self._construct_channel(channels)
        self.send_pwm(channels)

    def control_FRU(self, AIL=0, ELE=0, THR=0, RUD=0, Mode=2):
        channels = [0] * 8
        channels[self.AIL[0]] = self.movement(self.AIL, AIL)
        channels[self.ELE[0]] = self.movement(self.ELE, ELE)
        channels[self.THR[0]] = self.movement2(self.THR, THR)
        channels[self.RUD[0]] = self.movement2(self.RUD, RUD)
        channels[self.mode[0]] = self.mode[Mode]
        self._construct_channel(channels)
        self.send_pwm(channels)

    def control_percent(self, AIL=0, ELE=0, THR=0, RUD=0, Mode=2):
        channels = [0] * 8
        channels[self.AIL[0]] = self.movement3(self.AIL, AIL)
        channels[self.ELE[0]] = self.movement3(self.ELE, ELE)
        channels[self.THR[0]] = self.control_THR(THR)
        channels[self.RUD[0]] = self.movement3(self.RUD, RUD)
        channels[self.mode[0]] = self.mode[Mode]
        self._construct_channel(channels)
        self.send_pwm(channels)

    def _construct_channel(self, channels):
        if config.drone['Model'] == 'HELI':
            channels[self.Rate[0]] = self.Rate[2]
            channels[self.PIT[0]] = THR2PIT(channels[self.THR[0]])
            # channels[self.PIT[0]] = self.PIT[0]
        else:
            channels[self.Aux1[0]] = self.Aux1[2]
            channels[self.Aux2[0]] = self.Aux2[2]
        channels[self.Switch[0]] = self.Switch[2]

    def movement(self, channel, sign=1):
        # sign in [-1,0,1]. By Gear
        index = self.subscribe('Gear')
        rate = config.drone['Gear'][index] / 100.0
        index = 2 + channel[5] * sign
        section = abs(channel[2] - channel[index])
        variation = int(channel[5] * section * rate)
        return channel[2] + sign * variation

    def movement2(self, channel, sign=1):
        # sign in [-1,0,1].  By TOML
        rate = channel[6] / 100.0
        index = 2 + channel[5] * sign
        section = abs(channel[2] - channel[index])
        variation = int(channel[5] * section * rate)
        return channel[2] + sign * variation

    def movement3(self, channel, percent=0):
        # -100 <= percent <= 100. By Percent of PWM
        sign = 0
        if percent < 0:
            sign = -1
        elif percent > 0:
            sign = 1
        rate = percent / 100.0
        index = 2 + channel[5] * sign
        section = abs(channel[2] - channel[index])
        variation = int(channel[5] * section * rate)
        result = channel[2] + variation
        return result

    def GradualTHR(self, begin, end):
        watcher = CancelWatcher()
        if begin <= end:
            while begin <= end and not watcher.IsCancel():
                self.control_percent(THR=begin)
                begin += 1
                time.sleep(0.05)
        else:
            while begin >= end and not watcher.IsCancel():
                self.control_percent(THR=begin)
                begin -= 1
                time.sleep(0.05)

    def control_THR(self, percent):
        # 0 <= percent <= 100
        THR = self.THR
        rate = percent / 100.0
        section = THR[4]
        if THR[5] < 0:
            rate = 1 - rate
        variation = int(section * rate)
        result = THR[1] + variation
        return result

    def arm(self):
        logger.info("Arming ...")
        if config.drone['Model'] == 'HELI':
            return
        self.control_stick(-1, -1, -1, 1)
        # time.sleep(2)
        # self.disarm()

    def disarm(self):
        logger.info('DisArmed ...')
        self.control_stick(THR=-1, Mode=2)

    def takeoff(self, alt=5):
        watcher = CancelWatcher()
        logger.info('Takeoff to {} m'.format(alt))
        if not config.has_module('Baro'):
            logger.warn('Baro is closed')
            return

        self.escalate(0, 60)

        while not watcher.IsCancel():
            currentAlt = self.get_alttitude(True)
            logger.debug('Current Altitude :{}'.format(currentAlt))
            if currentAlt is None:
                logger.error('Baro is not health')
                break
            if currentAlt > alt * 0.95:
                logger.info('Reached Altitude :{}'.format(currentAlt))
                break
            time.sleep(.1)

        self.brake()

    def land(self):
        logger.info('Landing...')
        if not config.has_module('Baro'):
            logger.warn('Baro is closed')
            return

        # self.control_FRU(0, 0, -1)
        # watcher = CancelWatcher()
        # time.sleep(3)
        # preAlt = self.get_altitude()
        # times = 0
        # while not watcher.IsCancel():
        #     currentAlt = self.get_altitude()
        #     print 'Current Altitude', currentAlt
        #     if currentAlt is None:
        #         self.brake()
        #         return -1

        #     if abs(currentAlt - preAlt) < 0.2:
        #         times += 1
        #     else:
        #         times = 0
        #     if times >= 5:
        #         break
        #     if currentAlt > alt * 0.9:
        #         print 'Reached Altitude'
        #         break
        # if not watcher.IsCancel():
        #     self.disarm()

    def up_metres(self, altitude, relative=True):
        if altitude <= 0:
            logger.warn('Altitude({}) is unvalid'.format(altitude))
            return
        if not config.has_module('Baro'):
            logger.warn('Baro is closed')
            return
        CAlt = self.get_altitude(False)
        if CAlt is None:
            logger.error('Baro is not health')
            return
        if relative:
            TAlt = CAlt + altitude
        else:
            IAlt = self.ORB._HAL['InitAltitude']
            if IAlt is None:
                logger.error('InitAltitude is null')
                return
            TAlt = IAlt + altitude
        if TAlt < CAlt:
            logger.warn(
                'TAlt({}) is less than CAlt ({}).'.format(TAlt, CAlt))
            return
        self.control_FRU(THR=1)
        watcher = CancelWatcher()
        while not watcher.IsCancel():
            CAlt = self.get_altitude(False)
            if CAlt is None or CAlt >= TAlt:
                break
            time.sleep(.1)
        self.brake()

    def down_metres(self, altitude, relative=True):
        if altitude <= 0:
            logger.warn('Altitude({}) is unvalid'.format(altitude))
            return
        if not config.has_module('Baro'):
            logger.warn('Baro is closed')
            return
        CAlt = self.get_altitude(False)
        if CAlt is None:
            logger.error('Barometre is not health')
            return

        TAlt = CAlt - altitude
        IAlt = self.ORB._HAL['InitAltitude']
        if IAlt is None:
            logger.error('InitAltitude is null')
            return
        if TAlt < IAlt + 1:
            logger.warn('TAltitude({}) is too low.'.format(TAlt - IAlt))
            return
        self.control_FRU(THR=-1)
        watcher = CancelWatcher()
        while not watcher.IsCancel():
            CAlt = self.get_altitude(False)
            if CAlt is None or CAlt <= TAlt:
                break
        self.brake()

    def yaw_left(self):
        self.control_FRU(RUD=-1)

    def yaw_right(self):
        self.control_FRU(RUD=1)

    def forward(self):
        logger.info('Forward...')
        self.control_FRU(ELE=1)

    def yaw_left_brake(self):
        logger.info('Yaw Left')
        self.control_FRU(RUD=-1)
        time.sleep(self.moveTime)
        self.brake()

    def yaw_right_brake(self):
        logger.info('Yaw Right')
        self.control_FRU(RUD=1)
        time.sleep(self.moveTime)
        self.brake()

    def forward_brake(self):
        logger.info('Forward')
        self.control_FRU(ELE=1)
        time.sleep(self.moveTime)
        self.brake()

    def backward_brake(self):
        logger.info('Backward')
        self.control_FRU(ELE=-1)
        time.sleep(self.moveTime)
        self.brake()

    def roll_left_brake(self):
        logger.info('Roll Left')
        self.control_FRU(AIL=-1)
        time.sleep(self.moveTime)
        self.brake()

    def roll_right_brake(self):
        logger.info('Roll Right')
        self.control_FRU(AIL=1)
        time.sleep(self.moveTime)
        self.brake()

    def up_brake(self):
        logger.info('Throttle Up')
        self.control_FRU(THR=1)
        time.sleep(self.moveTime)
        self.brake(1)

    def down_brake(self):
        logger.info('Throttle Down')
        self.control_FRU(THR=-1)
        time.sleep(self.moveTime)
        self.brake(1)

    def send_pwm(self, channels):
        # self._debug(channels)
        # self._debug(self.analysis_channels(channels))
        self.publish('ChannelsOutput', channels)

    def analysis_channels(self, channels):
        a = [x - y for x, y in zip(channels, self.subscribe('LoiterPWM'))]
        return [x * y for x, y in zip(a, self.Phase())]

    def isStop(self, heading, target, sign):
        diff = angle_diff(heading, target, sign)

        return False if diff <= 180 and diff > 2 else True

    def condition_yaw(self, heading):
        """
        0<=heading<360 (anti-clockwise)
        """
        if heading <= 0 or heading >= 360:
            return

        watcher = CancelWatcher()
        CYaw = self.get_heading()
        if CYaw is None:
            return
        # Relative angle to heading
        target_angle = angle_diff(CYaw, heading)
        TurnAngle = angle_diff(CYaw, target_angle)

        if TurnAngle >= 0 and TurnAngle <= 180:
            is_cw = 1
            logger.debug('Turn left {}'.format(TurnAngle))
            self.yaw_left()
        else:
            is_cw = -1
            logger.debug('Turn right {}'.format(360 - TurnAngle))
            self.yaw_right()

        logger.debug("Target Angle: %d" % target_angle)
        while not watcher.IsCancel():
            CYaw = self.get_heading()
            if CYaw is None:
                break
            if self.isStop(CYaw, target_angle, is_cw):
                break
            # logger.debug('{},{}'.format(CYaw, target_angle))
        # logger.debug("Before Angle:{}".format(self.get_heading()))
        self.brake()
        logger.debug("After  Angle:{}".format(self.get_heading()))

    def navigation(self, target):
        self.publish('Target', target)
        watcher = CancelWatcher()
        radius = self.radius
        frequency = self.frequence
        CLocation = self.get_location()
        CYaw = self.get_heading()
        if CLocation is None or CYaw is None or target is None:
            return

        init_angle = angle_heading_target(CLocation, target, CYaw)
        self.condition_yaw(init_angle)

        while not watcher.IsCancel():
            CLocation = self.get_location()
            CYaw = self.get_heading()
            if CLocation is None or CYaw is None:
                break
            distance = get_distance_metres(CLocation, target)
            angle = angle_heading_target(CLocation, target, CYaw)

            if not self.InAngle(angle, 90) or distance <= radius:
                logger.info("Reached Target!")
                break

            EAngle = int(math.degrees(math.asin(radius / distance)))

            self._debug('{} {} {}'.format(distance, angle, EAngle))

            if not self.InAngle(angle, max(EAngle, self.Epsilon)):
                self.brake()
                self.condition_yaw(angle)
            self.forward()
            time.sleep(frequency)
            # raw_input('next')
        self.brake()

    def navigation1(self, target):
        self.publish('Target', target)
        watcher = CancelWatcher()
        radius = self.radius
        frequency = self.frequence

        CLocation = self.get_location()
        CYaw = self.get_heading()
        if CLocation is None or CYaw is None or target is None:
            return

        init_angle = angle_heading_target(CLocation, target, CYaw)
        self.condition_yaw(init_angle)

        while not watcher.IsCancel():
            CLocation = self.get_location()
            CYaw = self.get_heading()
            if CLocation is None or CYaw is None:
                break
            distance = get_distance_metres(CLocation, target)
            angle = angle_heading_target(CLocation, target, CYaw)

            if not self.InAngle(angle, 90) or distance <= radius:
                # if distance <= radius:
                logger.info("Reached Target Waypoint!")
                break
            EAngle = int(math.degrees(math.asin(radius / distance)))

            self._debug('{} {} {}'.format(distance, angle, EAngle))

            if self.InAngle(angle, max(EAngle, self.Epsilon)):
                self.control_FRU(ELE=1)
            else:
                if angle > EAngle and angle <= 90:
                    logger.debug('Roll Left')
                    self.control_FRU(AIL=-1, ELE=1)
                elif angle >= 270 and angle < 360 - EAngle:
                    logger.debug('Roll Right')
                    self.control_FRU(AIL=1, ELE=1)
                else:
                    self.brake()
                    self.condition_yaw(angle)
            time.sleep(frequency)
            # raw_input('next')
        self.brake()

    def navigation2(self, target):
        self.publish('Target', target)
        watcher = CancelWatcher()
        radius = self.radius
        frequency = 1
        CLocation = self.get_location()
        CYaw = self.get_heading()
        if CLocation is None or CYaw is None or target is None:
            return

        init_angle = angle_heading_target(CLocation, target, CYaw)
        self.condition_yaw(init_angle)

        while not watcher.IsCancel():
            CLocation = self.get_location()
            CYaw = self.get_heading()
            if CLocation is None or CYaw is None:
                break
            distance = get_distance_metres(CLocation, target)
            angle = angle_heading_target(CLocation, target, CYaw)

            self._debug('{} {}'.format(distance, angle))

            if not self.InAngle(angle, 90) or distance <= radius:
                logger.info("Reached Target!")
                break

            self.forward()
            time.sleep(frequency)
            # raw_input('next')
        self.brake()

    def InAngle(self, angle, EAngle):
        if angle < 360 - EAngle and angle > EAngle:
            return False
        else:
            return True

    def Guided(self):
        target = self.get_target()
        if target is None:
            logger.warn("Target is None!")
            return
        self.publish('Mode', 'GUIDED')

        self.navigation(target)
        self.publish('Mode', 'Loiter')
        self.publish('Target', None)

    def RTL(self):
        target = self.get_home()
        if target is None:
            logger.warn("Home is None!")
            return
        self.publish('Mode', 'RTL')

        self.navigation(target)
        # self.land()
        self.publish('Mode', 'STAB')

    def Route(self, info):
        self.wp.Route(info)
        # self.Auto()

    def Auto(self):
        if self.wp.isNull():
            logger.info('Waypoint is None')
            return
        self.publish('Mode', 'Auto')
        watcher = CancelWatcher()
        for point in self.wp.remain_wp():
            if watcher.IsCancel():
                break

            self.navigation(point)
            self.wp.add_number()

        self.publish('Mode', 'Loiter')
        self.publish('Target', None)
        self.wp.clear()

    def Cancel(self):
        CancelWatcher.Cancel = True
        time.sleep(.1)
        self.brake()

if __name__ == "__main__":
    from AF_uORB.uORB import uORB
    from lib.tools import Watcher

    ORB = uORB()
    Watcher()

    if config.has_module('Sbus'):
        # Initialize SBUS
        from AF_Sbus.sender import sbus_start
        sbus_start(ORB)

    if config.has_module('Compass'):
        # Initialize Compass
        from AF_Sensors.compass import compass_start
        compass_start(ORB)

    if config.has_module('GPS'):
        # Initialize GPS
        from AF_Sensors.GPS_module import GPS_start
        GPS_start(ORB)

    if config.has_module('Baro'):
        # Initialize Barometre
        from AF_Sensors.Baro import Baro_start
        Baro_start(ORB)

    if config.has_module('IMU'):
        # Initialize IMU
        from AF_Sensors.IMU import IMU_start
        IMU_start(ORB)

    # Save FlightLog to SD card
    # ORB.start()

    # Initialize UAV
    vehicle = Vehicle(ORB)

    for c in config.commands:
        enter = raw_input(c + '?').strip()

        if enter == 'c' or enter == 'C':
            continue
        elif enter == 'b' or enter == 'B':
            break
        else:
            command = 'vehicle.' + c
            # print 'Execute command ->', command
            try:
                eval(command)
            except Exception:
                info = sys.exc_info()
                print "{0}:{1}".format(*info)
                vehicle.Cancel()

    print 'Completed'