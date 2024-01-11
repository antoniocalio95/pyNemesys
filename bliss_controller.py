# -*- coding: utf-8 -*-
#
# This file is part of the bliss project
#
# Copyright (c) 2015-2023 Beamline Control Unit, ESRF
# Distributed under the GNU LGPLv3. See LICENSE for more info.

from bliss.controllers.motor import Controller
from bliss.common.axis import AxisState
from pyNemesys_linux import Nemesys


class TangoMotorController(Controller):
    """
    Controller for tango motor
    """

    def __init__(self, config, *args, **kwargs):
        tango_server_config = config.get("tango-server")
        self._tango_name = tango_server_config.get("tango_name")
        if self._tango_name is None:
            raise RuntimeError('Missing key "tango_name"')
        self._proxy = None
        super().__init__(*args, **kwargs)

    def _initialize(self):
        self._proxy = DeviceProxy(self._tango_name)
        try:
            self._proxy.ping()
        except DevFailed:
            self._proxy = None
            raise

    def initialize_axis(self, axis):
        self._proxy.initialize_axis(axis.name)

    def get_axis_info(self, axis):
        return self._proxy.get_axis_info(axis.name)

    def read_position(self, axis):
        return self._proxy.read_position(axis.name)

    def set_position(self, axis, new_position):
        self._proxy.set_position(f"{axis.name} {new_position}")
        return self.read_position(axis)

    def read_acceleration(self, axis):
        return self._proxy.read_acceleration(axis.name)

    def set_acceleration(self, axis, new_acceleration):
        self._proxy.set_acceleration(f"{axis.name} {new_acceleration}")
        return self.read_acceleration(axis)

    def read_velocity(self, axis):
        return self._proxy.read_velocity(axis.name)

    def set_velocity(self, axis, new_velocity):
        self._proxy.set_velocity(f"{axis.name} {new_velocity}")
        return self.read_velocity(axis)

    def state(self, axis):
        _state = self._proxy.axis_state(axis.name)
        if _state == DevState.ON:
            log_debug(self, f"{axis.name} READY")
            return AxisState("READY")
        if _state == DevState.MOVING:
            log_debug(self, f"{axis.name} MOVING")
            return AxisState("MOVING")
        if _state == DevState.DISABLE:
            log_debug(self, f"{axis.name} DISABLED")
            return AxisState("DISABLED")
        return AxisState("READY")
    
    def start_one(self, motion):
        """This is he command that actually moves the motor"""
        self._proxy.start_one(motion.target_pos).decode()
    
    def stop(self, axis):
        self._proxy.stop(axis.name)

