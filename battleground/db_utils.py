"""
Script to upload test teams into the db, and create a match between them.
Will also create a docker-compose file based on a template, that will
use the appropriate images for the agents, and pass the match_id as
an environment variable to the 'battleground' container.
"""


import datetime

from battleground.schema import session, Team, Match, Tournament


def create_db_team(name, members, dbsession=session):
    """
    Create a new team in the db after first checking if it already exists
    """
    existing_teams = dbsession.query(Team).all()
    for t in existing_teams:
        if t.team_name == name and t.team_members == members:
            print("Team already exists")
            return t.team_id
    print("Creating new team {}".format(name))
    new_team = Team()
    new_team.team_name = name
    new_team.team_members = members
    dbsession.add(new_team)
    dbsession.commit()
    return new_team.team_id


def create_db_tournament(teams, dbsession=session):
    """
    Create a new tournament for each day.
    """
    print("Creating new tournament")
    tourn = Tournament()
    tourn.tournament_time = datetime.datetime.now()
    existing_teams = dbsession.query(Team).all()

    for t in existing_teams:
        if t.team_name in teams:
            tourn.teams.append(t)
    dbsession.add(t)
    dbsession.commit()
    return tourn.tournament_id


def get_db_tournament(tournament_id, dbsession=session):
    """
    Return the Tournament object given the id
    """
    return (
        dbsession.query(Tournament)
        .filter_by(tournament_id=tournament_id)
        .first()
    )


def create_db_match(
    pelican_team,
    pelican_agent,
    panther_team,
    panther_agent,
    game_config="10x10_balanced.json",
    num_games=10,
    tournament_id=None,
    check_for_existing=False,
    dbsession=session,
):
    """
    Create a new match in the db after checking if it already exists.
    If check_for_existing is True and a match between the same teams
    and agents exists, return the match_id.  Otherwise, make a new match.
    """
    if check_for_existing:
        existing_matches = dbsession.query(Match).all()
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
    # if given team names for pelican and panther, attach the Teams.
    if pelican_team:
        pelican = (
            dbsession.query(Team).filter_by(team_name=pelican_team).first()
        )
        if not pelican:
            raise RuntimeError(
                "Unable to find pelican team {} in db".format(pelican_team)
            )
        new_match.pelican_team = pelican
    if panther_team:
        panther = (
            dbsession.query(Team).filter_by(team_name=panther_team).first()
        )
        if not panther:
            raise RuntimeError(
                "Unable to find panther team {} in db".format(panther_team)
            )
        new_match.panther_team = panther
    # fill in the other fields
    new_match.pelican_agent = pelican_agent
    new_match.panther_agent = panther_agent
    new_match.game_config = game_config
    new_match.match_time = datetime.datetime.now()
    new_match.num_games = num_games
    new_match.logfile_url = "empty_for_now"
    # see if we have a tournament to assign the match to
    if tournament_id:
        tournament = get_db_tournament(tournament_id, dbsession)
        new_match.tournament = tournament
        dbsession.add(tournament)
    dbsession.add(new_match)
    dbsession.commit()
    return new_match.match_id


def match_finished(match_id, dbsession=session):
    """
    Query the database for the match with match_id,
    see if it is finished (num_games == len(completed games))
    """
    match = dbsession.query(Match).filter_by(match_id=match_id).first()
    if not match:
        raise RuntimeError("Match {} not found in db".format(match_id))
    return match.is_finished
