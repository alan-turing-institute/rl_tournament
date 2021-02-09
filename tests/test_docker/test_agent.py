#!/usr/bin/env python

import sys
import json
from battleground.combatant import load_combatant
from battleground.schema import deserialize_state

agent_type = sys.argv[1]
agent_path = sys.argv[2]
agent_name = sys.argv[3]
basic_agents_filepath = "////"

allowed_actions = {"PANTHER": [], "PELICAN": []}


agent = load_combatant(agent_path, agent_type, basic_agents_filepath)
if agent_type == "PELICAN":
    state = deserialize_state(
        json.load(open("states/state_10x10_pelican.json"))
    )
else:
    state = deserialize_state(
        json.load(open("states/state_10x10_panther.json"))
    )

action = agent.getAction(state)
if action not in allowed_actions[agent_type]:
    raise RuntimeError("NO!")
