"""
Test battleground.py module
"""

import os
import json
import datetime

from battleground.conftest import test_session_scope, remove_test_db
from battleground.schema import Match
from battleground.db_utils import create_db_match
from battleground.battleground import (
    Battleground,
    Battle,
)


def test_create_battleground():
    """
    test that we can create a battleground (Match)
    """
    with test_session_scope() as ts:
        match_id = create_db_match(
            pelican_team=None,
            panther_team=None,
            pelican_agent="dummy",
            panther_agent="dummy",
            game_config="dummy",
            dbsession=ts,
        )

        bg = Battleground(match_id=match_id, dbsession=ts)
        assert isinstance(bg, Battleground)


# def test_battle():
#    """
#    tests battle loading
#    """
#
#    config_file_path = os.path.join(
#        os.getenv("PLARKAICOMPS"),
#        "plark-game",
#        "plark_game",
#        "game_config",
#        "10x10/balanced.json",
#    )
#
#    with open(config_file_path) as f:
#        game_config = json.load(f)
#
#    battle = Battle(game_config)
#
#    assert isinstance(battle, Battle)
