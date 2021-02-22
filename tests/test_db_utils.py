from battleground.conftest import test_session_scope
from battleground.schema import Team, Agent, Match
from battleground.db_utils import (
    create_db_team,
    create_db_agent,
    create_db_match,
)


def test_create_team():
    """
    Add a team to the db
    """
    with test_session_scope() as tsession:
        team_id = create_db_team("a_team", "team_members", dbsession=tsession)
        assert isinstance(team_id, int)
        nt = tsession.query(Team).filter_by(team_id=team_id).first()
        assert isinstance(nt, Team)
        assert nt.team_name == "a_team"
        assert nt.team_members == "team_members"


def test_create_agent():
    """
    Add an agent and its team to the db
    """
    with test_session_scope() as tsession:
        agent_id = create_db_agent(
            "test_team:pelican_agent", "pelican", dbsession=tsession
        )
        assert isinstance(agent_id, int)
        nt = tsession.query(Agent).filter_by(agent_id=agent_id).first()
        assert isinstance(nt, Agent)
        assert nt.agent_name == "test_team:pelican_agent"
        assert nt.agent_type == "pelican"
        assert nt.team.team_name == "test_team"


def test_create_match():
    """
    Add two agents and a match to the db
    """
    with test_session_scope() as tsession:
        _ = create_db_agent(
            "test_team:pelican_agent", "pelican", dbsession=tsession
        )
        _ = create_db_agent(
            "test_team:panther_agent", "panther", dbsession=tsession
        )
        match_id = create_db_match(
            pelican_agent="test_team:pelican_agent",
            panther_agent="test_team:panther_agent",
            dbsession=tsession,
        )
        nm = tsession.query(Match).filter_by(match_id=match_id).first()
        assert isinstance(nm, Match)
        assert nm.pelican_agent.agent_name == "test_team:pelican_agent"
        assert nm.panther_agent.agent_name == "test_team:panther_agent"
