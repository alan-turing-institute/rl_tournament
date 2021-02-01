import os
import datetime
import json

from battleground.battleground import Battle


def test_simple_battle():
    """
    A unit test to perform a simple battle (game). Combantants
        are defined in test_configs/10x10_balanced.json and the
        outcome is saved as a video.
    """

    config_file_path = os.path.join(
        "test_configs",
        "10x10_balanced.json",
    )

    video_file_path = os.path.join(
        "test_outputs",
        "test_simple_battle%s.mp4"
        % str(datetime.datetime.now().strftime("%Y%m%d_%H%M%S")),
    )

    with open(config_file_path) as f:
        game_config = json.load(f)

    battle = Battle(game_config)

    battle.play(video_file_path)

    assert os.path.isfile(video_file_path)


if __name__ == "__main__":

    test_simple_battle()
