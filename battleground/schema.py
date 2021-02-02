"""
Marshmallow schemas for serializing/deserializing game objects
so that they can be sent as JSON
"""

from marshmallow import Schema, fields, post_load

import plark_game
from plark_game.classes.sonobuoy import Sonobuoy
from plark_game.classes.torpedo import Torpedo

class SonobuoySchema(Schema):
    type = fields.Str()
    col = fields.Int(allow_none=True)
    row = fields.Int(allow_none=True)
    range = fields.Int()
    state = fields.Str()
    size = fields.Int()

    @post_load
    def make_sonobuoy(self, data, **kwargs):
        sb = Sonobuoy(data["range"])
        sb.type = data["type"]
        sb.col = data["col"]
        sb.row = data["row"]
        sb.state = data["state"]
        sb.size = data["size"]
        return sb


class TorpedoSchema(Schema):
    id = fields.Str(allow_none=True)
    type = fields.Str()
    col = fields.Int(allow_none=True)
    row = fields.Int(allow_none=True)
    turn = fields.Int()
    size = fields.Int()
    speed = fields.Int(allow_none=True)
    searchRadius = fields.Int(allow_none=True)

    @post_load
    def make_torpedo(self, data, **kwargs):
        t = Torpedo(**data)
        return t


def serialize_state(state):
    """
    Convert any Torpedo or Sonobuoy objects in the state
    into their JSON representations.
    """
    output_json = {}
    sbs = SonobuoySchema()
    ts = TorpedoSchema()
    for k, v in state.items():
        if k != "pelican_loadout":
            output_json[k] = v
        else:
            loadout = []
            for obj in v:
                if isinstance(obj, plark_game.classes.sonobuoy.Sonobuoy):
                    loadout.append(sbs.dump(obj))
                elif isinstance(obj, plark_game.classes.torpedo.Torpedo):
                    loadout.append(ts.dump(obj))
            output_json[k] = loadout
    return output_json


def deserialize_state(json_state):
    """
    Convert JSON representation of state in to version
    containing instances of Torpedo and Sonobuoy classes.
    """
    output_json = {}
    sbs = SonobuoySchema()
    ts = TorpedoSchema()
    for k, v in json_state.items():
        if k != "pelican_loadout":
            output_json[k] = v
        else:
            loadout = []
            for obj in v:
                if isinstance(obj, dict) and "type" in obj.keys() \
                   and obj["type"] == "SONOBUOY":
                    loadout.append(sbs.load(obj))
                elif isinstance(obj, dict) and "type" in obj.keys() \
                   and obj["type"] == "TORPEDO":
                    loadout.append(ts.load(obj))
            output_json[k] = loadout
    return output_json
