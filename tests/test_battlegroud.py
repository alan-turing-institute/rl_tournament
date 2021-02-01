"""
Test battleground.py module
"""

import os
import json

from battleground.battleground import (
    Battle,
)


def test_battle():
    """
    tests battle loading
    """

    config_file_path = os.path.join(
        os.getenv("PLARKAICOMPS"),
        "plark-game",
        "plark_game",
        "game_config",
        "10x10/balanced.json",
    )

    with open(config_file_path) as f:
        game_config = json.load(f)

    battle = Battle(game_config)

    assert isinstance(battle, Battle)
