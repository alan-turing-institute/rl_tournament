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
    pelican_team, pelican_agent, panther_team, panther_agent, game_config
):
    """
    Create a new match in the db after checking if it already exists
    """
    existing_matches = session.query(Match).all()
    for m in existing_matches:
        if (
            m.pelican_team.team_name == pelican_team
            and m.panther_team.team_name == panther_team
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


def write_docker_compose(match_id):
    """
    Get a Match out of the DB and build its corresponding docker-compose
    file, setting environment vars for the Battleground.
    """
    match = session.query(Match).filter_by(match_id=match_id).first()
    if not match:
        raise RuntimeError("Couldn't find match {}".format(match_id))
    dc_text = open("docker-compose-template.yml").read()
    dc_text = dc_text.replace("<MATCH_ID>", str(match_id))
    dc_text = dc_text.replace("<PELICAN_IMAGE>", match.pelican_agent)
    dc_text = dc_text.replace("<PANTHER_IMAGE>", match.panther_agent)

    with open("docker-compose-match{}.yml".format(match_id), "w") as outfile:
        outfile.write(dc_text)


if __name__ == "__main__":
    teamid1 = create_team("TeamDisney", "Mickey Mouse, Donald Duck")
    teamid2 = create_team("TeamWarnerBros", "Bugs Bunny, Road Runner")
    matchid = create_match(
        pelican_team="TeamDisney",
        pelican_agent="plark_hunt/team_test:latest",
        panther_team="TeamWarnerBros",
        panther_agent="plark_hunt/team_test:latest",
        game_config="10x10_balanced.json",
    )
    write_docker_compose(matchid)
