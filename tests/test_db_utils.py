from battleground.conftest import test_session_scope
from battleground.schema import Team, Tournament, Match, Game
from battleground.db_utils import (
    create_db_team,
    create_db_tournament,
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
