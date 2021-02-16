import os

from battleground.battleground import Battleground

if __name__ == "__main__":
    if "MATCH_ID" not in os.environ.keys():
        raise RuntimeError("MATCH_ID not found in environment")
    match_id = os.environ["MATCH_ID"]

    bg = Battleground(match_id=match_id)

    bg.setup_games()
    bg.listen_for_ready()
    bg.play()
