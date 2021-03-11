#!/usr/bin/env python

"""
Frontend for the Turing Plark tournaments
"""
import os
import sys
import time
import json
import requests
from flask import Flask, render_template
from tournament_plot import get_tournament_fig

BASE_URL = os.environ["API_BASE_URL"]

CACHE_DIR = "data"


app = Flask(__name__)


def get_data(data_type, data_id):
    """
    Retrieve match or game data, either from cache or from API.
    If retrieving for the first time, and it is complete, cache it.

    Parameters:
    ===========
    data_type: str, must be "matches" or "games"
    data_id: int, match_id or game_id
    """
    filepath = os.path.join(CACHE_DIR,"{}_{}.json".format(data_type,data_id))
    if not os.path.exists(filepath):
        # retrieve from API
        url = BASE_URL+"/{}/{}".format(data_type, data_id)
        r = requests.get(url)
        if r.status_code is not 200:
            raise RuntimeError("Couldn't reach API {}".format(url))
        data = r.json()
        if is_data_complete(data, data_type):
            # cache the data in a json file
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(filepath, "w") as output_json:
                json.dump(data, output_json)
        else:
            print("Data is not complete")
        return data
    else:
        # cached data already exists
        data = json.load(open(filepath))
        return data


def is_data_complete(data_dict, data_type):
    """
    data_type must be 'matches' or 'games'
    """
    if data_type == "games":
        return len(data_dict) > 0
    elif data_type == "matches":
        return data_dict["panther_score"] \
            + data_dict["pelican_score"] \
            == data_dict["num_games"]
    else:
        return False



@app.route("/")
def homepage():
    """
    basic homepage - list the interesting tournaments.
    """
    return render_template("index.html")


@app.route("/tournaments")
def tournaments():
    """
    basic homepage - options to view results table or run a new test.
    """
    r = requests.get(BASE_URL+"/tournaments")
    if r.status_code is not 200:
        raise RuntimeError("Couldn't reach API")

    tournaments = r.json()
    return render_template("tournamentlist.html", tournaments=tournaments,
                           base_url=BASE_URL)


@app.route("/tournament/<tid>")
def tournament(tid):
    """
    basic homepage - options to view results table or run a new test.
    """
    url = BASE_URL+"/tournaments/{}".format(tid)
    r = requests.get(url)
    if r.status_code is not 200:
        raise RuntimeError("Couldn't reach API {}".format(url))
    match_ids = r.json()["matches"]
    ## prepare a dict to turn into a plot
    panther_agents = []
    pelican_agents = []
    agent_type = []
    score = []
    configs = []
    logfiles = []
    # loop over all the matches in the tournament
    matches = []
    for mid in match_ids:
        match_data = get_data("matches", mid)
        for _ in range(2):
            panther_agents.append(match_data["panther"])
            pelican_agents.append(match_data["pelican"])
            configs.append(match_data["config"])
            logfiles.append(match_data["logfile"])
        agent_type.append("panther")
        score.append(match_data["panther_score"])
        agent_type.append("pelican")
        score.append(match_data["pelican_score"])
        # data for the html table
        matches.append(match_data)
    match_dict = {
        "panther": panther_agents,
        "pelican": pelican_agents,
        "agent_type": agent_type,
        "score": score,
        "configs": configs,
        "logfiles": logfiles
    }
    plot_div = get_tournament_fig(match_dict)
    return render_template(
        "tournament.html", tid=tid,
        plot=plot_div,
        matches=matches
    )


@app.route("/match/<mid>")
def match(mid):
    """
    Information about a the games in a specific match
    """
    url = BASE_URL+"/matches/{}".format(mid)
    r = requests.get(url)
    if r.status_code is not 200:
        raise RuntimeError("Couldn't reach API {}".format(url))
    game_ids = r.json()["games"]
    games = []
    for gid in game_ids:
        game_data = get_data("games", gid)
        games.append(game_data)
    return render_template(
        "match.html", mid=mid,
        games=games
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
