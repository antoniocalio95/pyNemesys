# -*- coding: utf-8 -*-
#
# This file is part of the bliss project
#
# Copyright (c) 2015-2023 Beamline Control Unit, ESRF
# Distributed under the GNU LGPLv3. See LICENSE for more info.
# Author: Antonino Calio'

from bliss.controllers.motor import Controller
from pyNemesys_linux import Nemesys


class Cetoni_Nemesys(Controller):
    """
    Controller for Cetoni Nemesys syringe pumps
    """

    def __init__(self, config, *args, **kwargs):
        nem_config = config.get("cetoni_nemesys")
        self._name = nem_config.get("name")
        self._node = nem_config.get("node")
        self._port = nem_config.get("url")
        self._stroke = nem_config.get("syringe_stroke")
        self._diameter = nem_config.get("syringe_diameter")
        self.pump = Nemesys(self._node, self._port, self._stroke, self._diameter)

        super().__init__(*args, **kwargs)

    def _initialize(self):
        return self.pump._nemesys_init()
    
    def finalize(self):
        self.pump._nemesys_disable()
        return self.pump._bus_close()

    def initialize_axis(self):
        pass

    def get_axis_info(self):
        return self.pump._print_info

    def read_position(self):
        return self.pump._get_position

    def set_position(self, new_position):
        self.pump._move_at_set_speed(new_position)
        return self.pump._print_info

    def read_acceleration(self, axis):
        pass

    def set_acceleration(self, axis, new_acceleration):
        pass

    def read_velocity(self, axis):
        return self.pump._get_set_speed()

    def set_velocity(self, new_velocity):
        self.pump._set_speed(new_velocity)
        return self.pump._get_set_speed()

    def state(self, axis):
        return self.pump._pump_state()
    
    def start_one(self, new_position, new_velocity):
        self.pump._move_to_position_speed(new_position, new_velocity)
    
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

