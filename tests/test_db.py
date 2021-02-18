import datetime
from battleground.conftest import test_session_scope, remove_test_db
from battleground.schema import Team, Tournament, Match, Game


def test_add_team():
    """
    Add a team to the db
    """
    with test_session_scope() as tsession:
        t = Team()
        t.team_name = "TestTeam"
        t.team_members = "Someone, something"
        tsession.add(t)
        tsession.commit()
        nt = tsession.query(Team).order_by(Team.team_id.desc()).first()
        assert isinstance(nt, Team)
        assert nt.team_name == "TestTeam"
        assert nt.team_members == "Someone, something"


def test_add_teams_tournament():
    """
    Add 2 teams to the db and a tournament for them to play
    """
    with test_session_scope() as tsession:
        t1 = Team()
        t1.team_name = "TestTeam1"
        t1.team_members = "Someone, something"
        t2 = Team()
        t2.team_name = "TestTeam2"
        t2.team_members = "Someone, something"
        tourn = Tournament()
        tourn.tournament_time = datetime.datetime.now()
        tourn.teams = [t1, t2]
        tsession.add(tourn)
        tsession.commit()
        ntourn = (
            tsession.query(Tournament)
            .order_by(Tournament.tournament_id.desc())
            .first()
        )
        assert isinstance(ntourn, Tournament)
        assert isinstance(ntourn.tournament_time, datetime.datetime)
        assert isinstance(ntourn.teams, list)
        assert ntourn.teams[0].team_name == "TestTeam1"
        assert len(t1.tournaments) == 1
        assert len(t2.tournaments) == 1


def test_add_teams_tournament_match():
    """
    Add 2 teams to the db and a tournament for them to play,
    containing one match
    """
    with test_session_scope() as tsession:
        t1 = Team()
        t1.team_name = "TestTeam1"
        t1.team_members = "Someone, something"
        t2 = Team()
        t2.team_name = "TestTeam2"
        t2.team_members = "Someone, something"
        tourn = Tournament()
        tourn.tournament_time = datetime.datetime.now()
        tourn.teams = [t1, t2]
        m = Match()
        m.match_time = datetime.datetime.now()
        m.game_config = "dummy"
        m.num_games = 10
        m.logfile_url = "dummy"
        m.pelican_team = t1
        m.panther_team = t2
        m.pelican_agent = "blah"
        m.panther_agent = "blah"
        tourn.matches.append(m)
        tsession.add(t1)
        tsession.add(t2)
        tsession.add(tourn)
        tsession.add(m)
        tsession.commit()
        # now query the match table
        nm = tsession.query(Match).order_by(Match.match_id.desc()).first()
        assert isinstance(nm, Match)
        assert isinstance(nm.pelican_team, Team)
        assert isinstance(nm.panther_team, Team)
        assert isinstance(nm.tournament, Tournament)


def test_add_match_games():
    """
    Add a Match, and some Games within it.
    """
    with test_session_scope() as tsession:
        m = Match()
        m.match_time = datetime.datetime.now()
        m.game_config = "dummy"
        m.num_games = 10
        m.logfile_url = "dummy"
        m.pelican_agent = "dummy"
        m.panther_agent = "dummy"
        games = []
        for i in range(10):
            games.append(Game())
            games[-1].game_time = datetime.datetime.now()
            games[-1].video_url = "dummy"
            games[-1].num_turns = 100
            games[-1].result_code = "WINCHESTER"
            games[-1].match = m
            tsession.add(games[-1])
        tsession.add(m)
        tsession.commit()
        nm = tsession.query(Match).order_by(Match.match_id.desc()).first()
        assert nm.is_finished
        assert nm.winner == "panther"
