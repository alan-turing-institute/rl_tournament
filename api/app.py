#!/usr/bin/env python

"""
API for returning info from the database
HTTP requests to the endpoints defined here will give rise
to calls to functions in api_utils.py
"""
from flask import Blueprint, Flask, jsonify
from flask_cors import CORS
from flask_session import Session

from api_utils import (
    list_agents,
    list_teams,
    list_tournaments,
    get_tournament,
    get_match,
    get_game,
    create_response,
)


class ApiException(Exception):
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["status"] = "error"
        rv["error"] = self.message
        return rv


# Use a flask blueprint rather than creating the app directly
# so that we can also make a test app

blueprint = Blueprint("rl_tournament", __name__)


@blueprint.errorhandler(ApiException)
def handle_exception(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@blueprint.route("/teams", methods=["GET"])
def get_team_list():
    """
    Return a list of all teams
    """
    team_list = list_teams()
    return create_response(team_list)


@blueprint.route("/tournaments", methods=["GET"])
def get_tournament_list():
    """
    Return a list of all tournaments
    """
    tournaments = list_tournaments()
    return create_response(tournaments)


@blueprint.route("/tournaments/<tid>", methods=["GET"])
def get_tournament_info(tid):
    """
    Return info on tournament with tournament_id == tid
    """
    tournament = get_tournament(tid)
    return create_response(tournament)


@blueprint.route("/agents/<team_name>", methods=["GET"])
def get_agent_list(team_name):
    """
    Return a list of all agents for a given team
    """
    agents = list_agents(team=team_name)
    return create_response(agents)


@blueprint.route("/pelicans/<tid>", methods=["GET"])
def get_pelican_list(tid):
    """
    Return a list of all agents for a given team
    """
    agents = list_agents(tournament=tid, agent_type="pelican")
    return create_response(agents)


@blueprint.route("/panthers/<tid>", methods=["GET"])
def get_panther_list(tid):
    """
    Return a list of all agents for a given team
    """
    agents = list_agents(tournament=tid, agent_type="panther")
    return create_response(agents)


@blueprint.route("/matches/<mid>", methods=["GET"])
def get_match_info(mid):
    """
    Return details of match with match_id == mid
    """
    match = get_match(mid)
    return create_response(match)


@blueprint.route("/games/<gid>", methods=["GET"])
def get_game_info(gid):
    """
    Returne details of game with game_id == gid
    """
    game = get_game(gid)
    return create_response(game)


def create_app(name=__name__):
    app = Flask(name)
    app.config["SESSION_TYPE"] = "filesystem"
    app.secret_key = "some_secret"
    CORS(app, supports_credentials=True)
    app.register_blueprint(blueprint)
    Session(app)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True)
