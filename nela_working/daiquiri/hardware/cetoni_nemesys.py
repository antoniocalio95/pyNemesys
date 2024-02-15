#!/usr/bin/env python
# -*- coding: utf-8 -*-
from daiquiri.core.hardware.abstract.cetoni_nemesys import Cetoni_Nemesys as AbstractNemesys
from daiquiri.core.hardware.bliss.object import BlissObject
from daiquiri.core.hardware.abstract import HardwareProperty

import logging

logger = logging.getLogger(__name__)


class Cetoni_Nemesys(BlissObject, AbstractNemesys):
    property_map = {
        "state": HardwareProperty("state"),
        "nodeID": HardwareProperty("_node"),
        "position": HardwareProperty("read_position"),
        "velocity": HardwareProperty("read_inst_velocity"),
        "is_valve_on": HardwareProperty("is_valve_open"),
        "is_moving": HardwareProperty("is_moving"),
        "target_reached": HardwareProperty("is_target_reached"),
    }

    callable_map = {
        "initialize": "initialize_axis",
        "enable": "_initialize",
        "stop": "stop",
        "state": "state",
        "info": "get_axis_info",
        "close": "finalize",
        "home": "home",
        "home_neg_lim": "home_neg_lim",
        "switch_valve": "switch_valve",
        "aspirate": "aspirate",
        "dose": "dose",
    }

