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

BASE_URL = os.environ["API_BASE_URL"]

app = Flask(__name__)

@app.route("/")
def homepage():
    """
    basic homepage - options to view results table or run a new test.
    """
    r = requests.get(BASE_URL+"/tournaments")
    if r.status_code is not 200:
        raise RuntimeError("Couldn't reach API")

    tournaments = r.json()
    return render_template("index.html", tournaments=tournaments,
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
    matches = []
    for mid in match_ids:
        url = BASE_URL+"/matches/{}".format(mid)
        r = requests.get(url)
        if r.status_code is not 200:
            raise RuntimeError("Couldn't reach API {}".format(url))
        matches.append(r.json())
    return render_template(
        "tournament.html", tid=tid,
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
        url = BASE_URL+"/games/{}".format(gid)
        r = requests.get(url)
        if r.status_code is not 200:
            raise RuntimeError("Couldn't reach API {}".format(url))
        games.append(r.json())
    return render_template(
        "match.html", mid=mid,
        games=games
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
