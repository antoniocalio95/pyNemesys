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
        "nodeID": HardwareProperty("nodeID"),
        "position": HardwareProperty("position"),
        "velocity": HardwareProperty("velocity"),
        "is_valve_on": HardwareProperty("is_valve_on"),
        "is_moving": HardwareProperty("is_moving"),
        "target_reached": HardwareProperty("target_reached"),
    }

    callable_map = {
        "initialize": "_initialize",
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

