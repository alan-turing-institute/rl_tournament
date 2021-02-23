"""
Script to upload test teams into the db, and create a match between them.
Will also create a docker-compose file based on a template, that will
use the appropriate images for the agents, and pass the match_id as
an environment variable to the 'battleground' container.
"""


import datetime

from battleground.schema import session, Team, Agent, Match, Tournament


def create_db_team(name, members="placeholder", dbsession=session):
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


def create_db_agent(agent_name, agent_type, dbsession=session):
    """
    Create a new agent in the db if it doesn't already exist.
    Attach it to a team, creating the team if that doesn't already exist.
    Assumes that the agent name follows the convention
    <<TEAM_NAME>>:<<TAG>>
    """
    if ":" not in agent_name:
        raise RuntimeError(
            "agent_name must be in format <<TEAM_NAME>>:<<TAG>>"
        )
    existing_agents = dbsession.query(Agent).all()
    for a in existing_agents:
        if a.agent_name == agent_name:
            print("Agent {} already exists".format(agent_name))
            return a.agent_id
    team_name, agent_tag = agent_name.split(":")
    # create_db_team will do the check for us if the team already exists
    tid = create_db_team(team_name, dbsession=dbsession)
    team = dbsession.query(Team).filter_by(team_id=tid).first()
    # make a new Agent
    a = Agent()
    a.agent_name = agent_name
    a.agent_type = agent_type
    a.team = team
    dbsession.add(a)
    dbsession.commit()
    return a.agent_id


def create_db_tournament(agents, dbsession=session):
    """
    Create a new tournament for each day.
    """
    print("Creating new tournament")
    tourn = Tournament()
    tourn.tournament_time = datetime.datetime.now()
    existing_agents = dbsession.query(Agent).all()

    for a in existing_agents:
        if a.agent_name in agents:
            tourn.agents.append(a)
    dbsession.add(a)
    dbsession.add(tourn)
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
    pelican_agent,
    panther_agent,
    game_config="10x10_balanced.json",
    num_games=10,
    tournament_id=None,
    check_for_existing=False,
    dbsession=session,
):
    """
    Create a new match in the db after checking if it already exists.
    If check_for_existing is True and a match between the same agents
    exists, return the match_id.  Otherwise, make a new match.

    Parameters
    ==========
    pelican_agent: str, name of the pelican agent
    panther_agent: str, name of the panther agent
    game_config: str, name of the json file containing game config
    num_games: int, number of Games in the Match
    tournament_id: int, ID of the tournament in the database
    check_for_existing: if True, don't create a new match if there is
                        an existing match between the same agents.
    dbsession: sqlalchemy.orm.session.Session, the database session.
               By default use the global "session", but may want to
               use a different session for testing.

    Returns
    =======
    match_id: int, ID of the existing or newly created match in the db.
    """
    if check_for_existing:
        existing_matches = dbsession.query(Match).all()
        for m in existing_matches:
            if (
                m.pelican_agent.agent_name == pelican_agent
                and m.panther_agent.agent_name == panther_agent
            ):
                print("Match already exists")
                return m.match_id
    print("Creating new match: {} {}".format(pelican_agent, panther_agent))

    # if given team names for pelican and panther, attach the Agents.
    pelican = None
    panther = None
    if pelican_agent:
        pelican = (
            dbsession.query(Agent).filter_by(agent_name=pelican_agent).first()
        )
        if not pelican:
            raise RuntimeError(
                "Unable to find pelican agent {} in db".format(pelican_agent)
            )

    if panther_agent:
        print("panther agent {}".format(panther_agent))
        panther = (
            dbsession.query(Agent).filter_by(agent_name=panther_agent).first()
        )
        if not panther:
            raise RuntimeError(
                "Unable to find panther agent {} in db".format(panther_agent)
            )

    # create the Match object
    new_match = Match()
    if pelican:
        new_match.pelican_agent = pelican
    if panther:
        new_match.panther_agent = panther
    # fill in the other fields
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
