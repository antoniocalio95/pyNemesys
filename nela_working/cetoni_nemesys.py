# -*- coding: utf-8 -*-
#
# This file is part of the bliss project
#
# Copyright (c) 2015-2023 Beamline Control Unit, ESRF
# Distributed under the GNU LGPLv3. See LICENSE for more info.
# Author: Antonino Calio'

from bliss.controllers.motor import Controller
from bliss.controllers.motors.pyNemesys_linux import Nemesys


class Cetoni_Nemesys(Controller):
    """
    Controller for Cetoni Nemesys syringe pumps
    """

    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self._name = config.get("name")
        self._node = config.get("node")
        self._port = str(config.get("url"))
        self._stroke = config.get("syringe_stroke")
        self._diameter = config.get("syringe_diameter")
        self.pump = Nemesys(self._node, b'/dev/ttyS0', self._stroke, self._diameter)

    def _initialize(self):
        return self.pump._nemesys_init()
    
    def finalize(self):
        self.pump._nemesys_disable()
        return self.pump._bus_close()

    def initialize_axis(self):
        pass

    def get_axis_info(self):
        return self.pump._print_info()

    def read_position(self):
        return self.pump._get_position()/self.pump.ul

    def set_position(self, new_position):
        self.pump._move_at_set_speed(new_position)
        return self.pump._print_info()

    def read_acceleration(self):
        pass

    def set_acceleration(self):
        pass

    def read_velocity(self):
        return self.pump._get_set_speed()

    def set_velocity(self, new_velocity):
        self.pump._set_speed(new_velocity)
        return self.pump._get_set_speed()

    def state(self):
        return self.pump._pump_state()

    def start_one(self):
        pass
    
    def aspirate(self, new_volume, new_velocity):
        curr_vol = int(self.pump._get_position()/self.pump.ul)
        new_vol = -abs(new_volume)
        if (curr_vol + new_vol) >= -500:
            self.pump._move_to_position_speed((curr_vol + new_vol), new_velocity)
        else:
            print("\nThe syringe is too full, aspirate less or empty it!\n")

    def dose(self, new_volume, new_velocity):
        curr_vol = int(self.pump._get_position()/self.pump.ul)
        new_vol = abs(new_volume)
        if (curr_vol + new_vol) <= 0:
            self.pump._move_to_position_speed((curr_vol + new_vol), new_velocity)
        else:
            print("\nThe syringe does not contain enough liquid, dose less or fill it up!\n")
    
    def stop(self):
        self.pump._halt()
        
    def home(self):
        return self.pump._reference_pos_lim()
    
    def home_neg_lim(self):
        return self.pump._reference_neg_lim()
    
    def is_moving(self):
        return self.pump._is_moving()
    
    def is_target_reached(self):
        return self.pump._is_target_reached()
    
    def is_valve_open(self):
        return self.pump._is_valve_open()
    
    def switch_valve(self):
        return self.pump._switch_valve()

