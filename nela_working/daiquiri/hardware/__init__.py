#!/usr/bin/env python
# -*- coding: utf-8 -*-
import importlib
import logging

from marshmallow import ValidationError, fields, validates_schema, post_load
from bliss.config.static import get_config

from daiquiri.core.hardware.abstract import ProtocolHandler
from daiquiri.core.hardware.bliss.object import BlissDummyObject
from daiquiri.core.schema.hardware import HOConfigSchema
from daiquiri.core.exceptions import InvalidYAML
from daiquiri.core.utils import loader


logger = logging.getLogger(__name__)

bl = logging.getLogger("bliss")
bl.disabled = True

bl = logging.getLogger("bliss.common.mapping")
bl.disabled = True


class BlissHOConfigSchema(HOConfigSchema):
    """The Bliss Hardware Object Config Schema"""

    address = fields.Str(metadata={"description": "Beacon object id"})
    type = fields.Str(metadata={"description": "Object type for objects without id"})

    @validates_schema
    def schema_validate(self, data, **kwargs):
        if not (data.get("address") or data.get("url")):
            raise ValidationError(
                "Object must have either an `address` or `url` defined"
            )

    @post_load
    def populate(self, data, **kwargs):
        """Generate the device address from its url"""
        if data.get("url"):
            _, address = data["url"].split("://")
            data["address"] = address

        return data


class BlissHandler(ProtocolHandler):
    """The bliss protocol handler

    Returns an instance of an abstracted bliss object

    The bliss protocol handler first checks the kwargs conform to the BlissHOConfigSchema
    defined above. This address is used to retrieve the  bliss object. Its class is then mapped
    to an abstract class and a bliss specific instance is created (see hardware/bliss/motor.py)
    """

    library = "bliss"

    _class_map = {
        "bliss.common.axis.Axis": "motor",
        "bliss.controllers.actuator.Actuator": "actuator",
        "bliss.controllers.multiplepositions.MultiplePositions": "multiposition",
        "bliss.common.shutter.BaseShutter": "shutter",
        "bliss.controllers.test.objectref.ObjectRef": "objectref",
        "bliss.controllers.intraled.Intraled": "intraled",
        "bliss.controllers.motors.cetoni_nemesys.Cetoni_Nemesys": "cetoni_nemesys",
        "tomo.tomoconfig.TomoConfig": "tomoconfig",
        "tomo.tomo_detectors.TomoDetectors": "tomodetectors",
        "tomo.tomo_imaging.TomoImaging": "tomoimaging",
        "tomo.optic.base_optic.BaseOptic": "tomooptic",
        "tomo.tomo_detector.TomoDetector": "tomodetector",
    }

    _class_name_map = {
        "EBV": "beamviewer",
        "ChannelFromConfig": "channelfromconfig",
        "volpi": "volpi",
        "TestObject": "test",
        "Fshutter": "shutter",
        "transmission": "transmission",
        "tango_attr_as_counter": "tango_attr_as_counter",
        "ShimadzuCBM20": "shimadzucbm20",
        "ShimadzuPDA": "shimadzupda",
        "ID26Attenuator": "attenuator_wago",
        "PresetManager": "presetmanager",
    }

    def get(self, **kwargs):
        try:
            kwargs = BlissHOConfigSchema().load(kwargs)
        except ValidationError as err:
            raise InvalidYAML(
                {
                    "message": "Bliss hardware object definition is invalid",
                    "file": "hardware.yml",
                    "obj": kwargs,
                    "errors": err.messages,
                }
            ) from err

        obj_type = kwargs.get("type")

        if obj_type == "activetomoconfig":
            # It's a global proxy without real instance
            class GlobalBlissObject:
                name = None

            obj = GlobalBlissObject()
        else:
            config = get_config()
            try:
                obj = config.get(kwargs.get("address"))
            except Exception:
                logger.exception(f"Couldn't get bliss object {kwargs.get('address')}")
                return BlissDummyObject(**kwargs)
        kwargs["obj"] = obj

        obj_type = kwargs.get("type")
        if obj_type is not None:
            return loader(
                "daiquiri.core.hardware.bliss",
                "",
                obj_type,
                **kwargs,
            )

        for bliss_mapping, mapped_class in self._class_map.items():
            bliss_file, bliss_class_name = bliss_mapping.rsplit(".", 1)
            # Some classes may not be available depending on the bliss version
            try:
                bliss_module = importlib.import_module(bliss_file)
                bliss_class = getattr(bliss_module, bliss_class_name)
            except ModuleNotFoundError:
                logger.warning(f"Could not find bliss module {bliss_mapping}")
                continue

            if isinstance(kwargs["obj"], bliss_class):
                return loader(
                    "daiquiri.core.hardware.bliss", "", mapped_class, **kwargs
                )

        cls = kwargs["obj"].__class__.__name__
        if cls in self._class_name_map:
            return loader(
                "daiquiri.core.hardware.bliss",
                "",
                self._class_name_map[cls],
                **kwargs,
            )

        logger.error("No class found for {cls}".format(cls=cls))
        return BlissDummyObject(**kwargs)
