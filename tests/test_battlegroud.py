"""
Test battleground.py module
"""
import os
import datetime
import json
import shutil

from battleground.conftest import test_session_scope
from battleground.battleground import Battleground, Battle
from battleground.db_utils import create_db_match
from battleground.schema import Game


def mock_agent_action(battle, agent_type):
    if agent_type == "PANTHER":
        print("mocking panther action for {}".format(battle))
        return "end"
    else:
        print("mocking pelican action for {}".format(battle))
        return "end"


def mock_setup_queues(battle):
    print("mocking setting up message queues for {}".format(battle))
    return True


def mock_load_config(blob_name, container_name):
    print("mocking reading json from {} {}".format(blob_name, container_name))
    config_file_path = os.path.join(
        os.path.dirname(__file__),
        "test_configs",
        "10x10_balanced.json",
    )
    return json.load(open(config_file_path))


def test_create_battleground():
    """
    test that we can create a battleground (Match)
    """
    with test_session_scope() as ts:
        match_id = create_db_match(
            pelican_agent=None,
            panther_agent=None,
            game_config="dummy",
            dbsession=ts,
        )

        bg = Battleground(match_id=match_id, dbsession=ts)
        assert isinstance(bg, Battleground)


def test_add_battles_to_battleground(monkeypatch):
    """
    test that we can create a battleground (Match)
    """
    with test_session_scope() as ts:
        match_id = create_db_match(
            pelican_agent=None,
            panther_agent=None,
            game_config="10x10_balanced",
            num_games=15,
            dbsession=ts,
        )

        bg = Battleground(match_id=match_id, dbsession=ts)
        monkeypatch.setattr(
            "battleground.battleground.read_json", mock_load_config
        )
        monkeypatch.setattr(
            "battleground.battleground.Battle.setup_message_queues",
            mock_setup_queues,
        )
        bg.setup_games()
        assert len(bg.activeGames) == 15


def test_simple_battle(monkeypatch):
    """
    A unit test to perform a simple battle (game). Combantants
        are defined in test_configs/10x10_balanced.json and the
        outcome is saved as a video.
    """
    config_file_path = os.path.join(
        os.path.dirname(__file__),
        "test_configs",
        "10x10_balanced.json",
    )
    output_path = os.path.join(os.path.dirname(__file__), "test_outputs")
    shutil.rmtree(output_path, ignore_errors=True)
    os.makedirs(output_path, exist_ok=True)
    video_file_path = os.path.join(
        output_path,
        "test_simple_battle%s.mp4"
        % str(datetime.datetime.now().strftime("%Y%m%d_%H%M%S")),
    )

    with open(config_file_path) as f:
        game_config = json.load(f)

    with test_session_scope() as tsession:
        monkeypatch.setattr(
            "battleground.battleground.Battle.setup_message_queues",
            mock_setup_queues,
        )
        battle = Battle(game_config)

        monkeypatch.setattr(
            "battleground.battleground.Battle.get_agent_action",
            mock_agent_action,
        )
        match_id = create_db_match(
            panther_agent=None, pelican_agent=None, dbsession=tsession
        )
        battle.play(match_id, video_file_path, dbsession=tsession)

        assert os.path.isfile(video_file_path)
        game = tsession.query(Game).order_by(Game.game_id.desc()).first()
        timenow = datetime.datetime.now()
        assert (timenow - game.game_time).days == 0
        assert (timenow - game.game_time).seconds < 5
        assert game.result_code == "BINGO"
