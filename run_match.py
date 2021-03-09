import os


from battleground.battleground import Battleground

if __name__ == "__main__":

    test = "NO_DB_TEST" in os.environ.keys() and os.environ["NO_DB_TEST"]

    if "MATCH_ID" not in os.environ.keys():
        raise RuntimeError("MATCH_ID not found in environment")
    match_id = os.environ["MATCH_ID"]

    arg_dict = {"match_id": match_id, "test": test}

    if "NUM_GAMES" in os.environ.keys():
        num_games = int(os.environ["NUM_GAMES"])
        arg_dict["num_games"] = num_games

    if "CONFIG_FILE" in os.environ.keys():
        config_file = os.environ["CONFIG_FILE"]
        arg_dict["config_file"] = config_file

    bg = Battleground(**arg_dict)

    bg.setup_games()
    bg.listen_for_ready()
    bg.play()
