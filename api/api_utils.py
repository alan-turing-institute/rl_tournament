"""
Functions used by the RL Tournament API
"""
from flask import jsonify

from battleground.schema import Team, Agent, Tournament, Match, Game, session


def create_response(orig_response):
    """
    Add headers to the response
    """
    response = jsonify(orig_response)
    response.headers.add(
        "Access-Control-Allow-Headers",
        "Origin, X-Requested-With, Content-Type, Accept, x-auth",
    )
    return response


def list_teams(dbsession=session):
    try:
        teams = dbsession.query(Team).all()
        team_names = [team.team_name for team in teams]
        dbsession.expunge_all()
        return team_names
    except:
        dbsession.rollback()
        return []


def list_agents(
    tournament="all", agent_type="all", team="all", dbsession=session
):
    """
    Return a list of agent names.
    """
    try:
        agents_query = dbsession.query(Agent)
        if agent_type != "all":
            agents_query = agents_query.filter_by(agent_type=agent_type)
        if team != "all":
            agents_query = agents_query.filter(Agent.team.has(team_name=team))
            agents = agents_query.all()
    except:
        dbsession.rollback()
        return []
    if tournament != "all":
        agents = [a for a in agents if int(tournament) in \
                  [t.tournament_id for t in a.tournaments]]
    agent_names = [agent.agent_name for agent in agents]
    dbsession.expunge_all()
    return agent_names


def list_tournaments(dbsession=session):
    try:
        tournaments = dbsession.query(Tournament).all()
    except:
        dbsession.rollback()
        return []
    tournament_list = [
        {
            "tournament_id": t.tournament_id,
            "tournament_time": t.tournament_time.isoformat().split(".")[0],
        }
        for t in tournaments
    ]
    dbsession.expunge_all()
    return tournament_list


def list_matches(tournament_id="all", dbsession=session):
    try:
        matches_query = dbsession.query(Match)
        if tournament_id != "all":
            matches_query = matches_query.filter_by(tournament_id=tournament_id)
        matches = matches_query.all()
    except:
        dbsession.rollback()
        return []
    match_list = [
        {
            "match_id": m.match_id,
            "match_time": m.match_time.isoformat().split(".")[0],
            "pelican": m.pelican_agent.agent_name,
            "panther": m.panther_agent.agent_name,
        }
        for m in matches
    ]
    dbsession.expunge_all()
    return match_list


def get_tournament(tournament_id, dbsession=session):
    try:
        tournament = (
            dbsession.query(Tournament)
            .filter_by(tournament_id=tournament_id)
            .first()
        )
    except:
        dbsession.rollback()
        return {}
    if not tournament:
        return {}
    tournament_info = {
        "tournament_id": tournament.tournament_id,
        "tournament_time": tournament.tournament_time.isoformat().split(".")[
            0
        ],
        "pelican_agents": [
            a.agent_name
            for a in tournament.agents
            if a.agent_type == "pelican"
        ],
        "panther_agents": [
            a.agent_name
            for a in tournament.agents
            if a.agent_type == "panther"
        ],
        "matches": [m.match_id for m in tournament.matches],
    }
    dbsession.expunge_all()
    return tournament_info


def get_match_id(tournament_id, panther, pelican, dbsession=session):
    try:
        match = (
            dbsession.query(Match)
            .filter_by(tournament_id=tournament_id)
            .filter(Match.pelican_agent.has(agent_name=pelican))
            .filter(Match.panther_agent.has(agent_name=panther))
            .first()
        )
    except:
        dbsession.rollback()
        return {}
    if not match:
        return {}
    match_id = match.match_id
    dbsession.expunge_all()
    return {"match_id": match_id}


def get_match(match_id, dbsession=session):
    try:
        match = dbsession.query(Match).filter_by(match_id=match_id).first()
    except:
        dbsession.rollback()
        return {}
    if not match:
        return {}
    match_info = {
        "match_id": match.match_id,
        "match_time": match.match_time.isoformat().split(".")[0],
        "pelican": match.pelican_agent.agent_name,
        "panther": match.panther_agent.agent_name,
        "logfile": match.logfile_url,
        "config": match.game_config,
        "num_games": match.num_games,
        "panther_score": match.score("panther"),
        "pelican_score": match.score("pelican"),
        "winner": match.winning_agent.agent_name if match.winning_agent else "Tie",
        "games": [g.game_id for g in match.games],
    }
    dbsession.expunge_all()
    return match_info


def get_game(game_id, dbsession=session):
    try:
        game = dbsession.query(Game).filter_by(game_id=game_id).first()
    except:
        dbsession.rollback()
        return {}
    if not game:
        return {}
    game_info = {
        "game_id": game.game_id,
        "game_time": game.game_time.isoformat().split(".")[0],
        "pelican": game.match.pelican_agent.agent_name,
        "panther": game.match.panther_agent.agent_name,
        "video": game.video_url,
        "num_turns": game.num_turns,
        "result_code": game.result_code,
        "winner": game.winner,
    }
    dbsession.expunge_all()
    return game_info
