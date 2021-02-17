"""
Script to upload test teams into the db, and create a match between them.
Will also create a docker-compose file based on a template, that will
use the appropriate images for the agents, and pass the match_id as
an environment variable to the 'battleground' container.
"""


import datetime

from battleground.schema import session, Team, Match


def create_team(name, members):
    """
    Create a new team in the db after first checking if it already exists
    """
    existing_teams = session.query(Team).all()
    for t in existing_teams:
        if t.team_name == name and t.team_members == members:
            print("Team already exists")
            return t.team_id
    print("Creating new team {}".format(name))
    new_team = Team()
    new_team.team_name = name
    new_team.team_members = members
    session.add(new_team)
    session.commit()
    return new_team.team_id


def create_match(
    pelican_team,
    pelican_agent,
    panther_team,
    panther_agent,
    game_config="10x10_balanced.json",
    check_for_existing=True,
):
    """
    Create a new match in the db after checking if it already exists.
    If check_for_existing is True and a match between the same teams
    and agents exists, return the match_id.  Otherwise, make a new match.
    """
    if check_for_existing:
        existing_matches = session.query(Match).all()
        for m in existing_matches:
            if (
                m.pelican_team.team_name == pelican_team
                and m.panther_team.team_name == panther_team
                and m.pelican_agent == pelican_agent
                and m.panther_agent == panther_agent
            ):
                print("Match already exists")
                return m.match_id
    print("Creating new match: {} {}".format(pelican_team, panther_team))
    new_match = Match()
    pelican = session.query(Team).filter_by(team_name=pelican_team).first()
    if not pelican:
        raise RuntimeError(
            "Unable to find pelican team {} in db".format(pelican_team)
        )
    new_match.pelican_team = pelican
    panther = session.query(Team).filter_by(team_name=panther_team).first()
    if not panther:
        raise RuntimeError(
            "Unable to find panther team {} in db".format(panther_team)
        )
    new_match.panther_team = panther
    new_match.pelican_agent = pelican_agent
    new_match.panther_agent = panther_agent
    new_match.game_config = game_config
    new_match.match_time = datetime.datetime.now()
    new_match.num_games = 10
    new_match.logfile_url = "empty_for_now"
    session.add(new_match)
    session.commit()
    return new_match.match_id


def match_finished(match_id):
    """
    Query the database for the match with match_id,
    see if it is finished (num_games == len(completed games))
    """
    match = session.query(Match).filter_by(match_id=match_id).first()
    if not match:
        raise RuntimeError("Match {} not found in db".format(match_id))
    return match.is_finished
