"""
Test combatant_panther.py module
"""
import os

from classes.pantherAgent import Panther_Agent
from classes.pelicanAgent import Pelican_Agent

from battleground.combatant import (
    load_combatant,
)


def test_load_combatant():
    """
    tests load_combatant routine
    """

    basic_agents_path = os.path.join(
        os.getenv("PLARKAICOMPS"),
        "plark-game",
        "plark_game",
        "agents",
        "basic",
    )

    agents_path = os.path.join(
        os.getenv("PLARKAIDATA"), "agents", "models", "test_20200325_184254"
    )

    panther_agent_name = ""
    panther_agent_path = os.path.join(
        agents_path, "PPO2_20200325_184254_panther"
    )
    panther = load_combatant(
        panther_agent_path, panther_agent_name, basic_agents_path
    )

    assert isinstance(panther, Panther_Agent)

    pelican_agent_name = ""
    pelican_agent_path = os.path.join(
        agents_path, "PPO2_20200325_184254_pelican"
    )
    pelican = load_combatant(
        pelican_agent_path, pelican_agent_name, basic_agents_path
    )

    assert isinstance(pelican, Pelican_Agent)
