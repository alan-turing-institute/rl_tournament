import os
import time

from battleground.battleground import Battleground


if __name__ == "__main__":
    if "MATCH_ID" not in os.environ.keys():
        raise RuntimeError("MATCH_ID not found in environment")
    match_id = os.environ["MATCH_ID"]

    bg = Battleground(match_id=match_id)
    # wait for rabbitmq queue to be ready
#    print("will wait for 2 mins")
#    time.sleep(120)
#    print("finished waiting - will setup games")
    bg.setup_games()
    bg.listen_for_ready()
    bg.play()
