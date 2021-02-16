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
    speed = fields.List(fields.Int(), allow_none=True)
    searchRadius = fields.Int(allow_none=True)

    @post_load
    def make_torpedo(self, data, **kwargs):
        t = Torpedo(**data)
        return t


def serializer(input_obj, mode="serialize"):
    """
    Recursive function to convert any Torpedo or Sonobuoy objects in the state
    into their JSON representations.

    Parameters
    ==========
    input_obj: could be dict, list, Torpedo, or Sonobuoy
    mode: str, must be "serialize" or "deserialize"

    Returns
    =======
    output: json-serialized, or de-serialized, version of the input_obj
    """
    if mode not in ["serialize", "deserialize"]:
        raise RuntimeError(
            "mode must be one of 'serialize', 'deserialize', not {}".format(
                mode
            )
        )
    output = None
    sbs = SonobuoySchema()
    ts = TorpedoSchema()
    if isinstance(input_obj, dict):
        # if we are deserializing, create Sonobuoy or Torpedo objects out of
        # dicts that have the appropriate 'type'
        if (
            mode == "deserialize"
            and "type" in input_obj.keys()
            and input_obj["type"] == "SONOBUOY"
        ):
            output = sbs.load(input_obj)
        elif (
            mode == "deserialize"
            and "type" in input_obj.keys()
            and input_obj["type"] == "TORPEDO"
        ):
            output = ts.load(input_obj)
        # for all other dicts, recursively look through their keys, values
        else:
            output = {}
            for k, v in input_obj.items():
                output[k] = serializer(v, mode)
    elif isinstance(input_obj, list):
        output = []
        for item in input_obj:
            output.append(serializer(item, mode))
    # if we have an instance of Sonobuoy or Torpedo,
    # use marshmallow schema to serialize
    elif isinstance(input_obj, plark_game.classes.sonobuoy.Sonobuoy):
        output = sbs.dump(input_obj)
    elif isinstance(input_obj, plark_game.classes.torpedo.Torpedo):
        output = ts.dump(input_obj)
    # any other type, just return as is
    else:
        output = input_obj
    return output


def serialize_state(game_state):
    return serializer(game_state, "serialize")


def deserialize_state(game_state):
    return serializer(game_state, "deserialize")
