#!/usr/bin/env python
# -*- coding: utf-8 -*-
from marshmallow import fields

from daiquiri.core.hardware.abstract import HardwareObject
from daiquiri.core.schema.hardware import HardwareSchema
from daiquiri.core.schema.validators import OneOf, RequireEmpty

import logging

logger = logging.getLogger(__name__)

PumpStates = ["DISABLED", "ENABLED", "QUICKSTOP", "FAULT"]


class NemesysPropertiesSchema(HardwareSchema):
    state = OneOf(PumpStates, metadata={"readOnly": True})
    nodeID = fields.Int()
    position = fields.Float()
    velocity = fields.Float()
    is_valve_on = fields.Bool()
    is_moving = fields.Bool()
    target_reached = fields.Bool()
    


class NemesysCallablesSchema(HardwareSchema):
    initialize = RequireEmpty()
    stop = RequireEmpty()
    state = RequireEmpty()
    info = RequireEmpty()
    close = RequireEmpty()
    home = RequireEmpty()
    home_neg_lim = RequireEmpty()
    switch_valve = RequireEmpty()
    aspirate = fields.List(fields.Float(), metadata={"many": True})
    dose = fields.List(fields.Float(), metadata={"many": True})

    
class Cetoni_Nemesys(HardwareObject):
    _type = "cetoni_nemesys"
    _state_ok = [PumpStates[1]]

    _properties = NemesysPropertiesSchema()
    _callables = NemesysCallablesSchema()

