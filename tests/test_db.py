import datetime
from battleground.conftest import test_session_scope
from battleground.schema import Team, Agent, Tournament, Match, Game


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


def test_add_team_agents():
    """
    Add a Team, with two Agents.
    """
    with test_session_scope() as tsession:
        t = Team()
        t.team_name = "test_team"
        t.team_members = "no-one"
        a1 = Agent()
        a1.agent_name = "test_team:pelican_latest"
        a1.agent_type = "pelican"
        a1.team = t
        a2 = Agent()
        a2.agent_name = "test_team:panther_latest"
        a2.agent_type = "panther"
        a2.team = t
        tsession.add(t)
        tsession.add(a1)
        tsession.add(a2)
        tsession.commit()
        nt = tsession.query(Team).order_by(Team.team_id.desc()).first()
        assert len(nt.agents) == 2
        assert isinstance(nt.agents[0], Agent)
        na = tsession.query(Agent).order_by(Agent.agent_id.desc()).first()
        assert isinstance(na.team, Team)
        assert na.team.team_name == "test_team"


def test_add_teams_agents_tournament():
    """
    Add 2 teams to the db, an agent each and a tournament for them to play
    """
    with test_session_scope() as tsession:
        t1 = Team()
        t1.team_name = "TestTeam1"
        t1.team_members = "Someone, something"
        t2 = Team()
        t2.team_name = "TestTeam2"
        t2.team_members = "Someone, something"
        a1 = Agent()
        a1.agent_name = "TestTeam1:panther_latest"
        a1.agent_type = "panther"
        a1.team = t1
        a2 = Agent()
        a2.agent_name = "TestTeam2:pelican_latest"
        a2.agent_type = "pelican"
        a2.team = t2
        tourn = Tournament()
        tourn.tournament_time = datetime.datetime.now()
        tourn.agents = [a1, a2]
        tsession.add(tourn)
        tsession.commit()
        ntourn = (
            tsession.query(Tournament)
            .order_by(Tournament.tournament_id.desc())
            .first()
        )
        assert isinstance(ntourn, Tournament)
        assert isinstance(ntourn.tournament_time, datetime.datetime)
        assert isinstance(ntourn.agents, list)
        assert len(ntourn.agents) == 2
        agent_names = [a.agent_name for a in ntourn.agents]
        assert "TestTeam1:panther_latest" in agent_names
        assert "TestTeam2:pelican_latest" in agent_names
        team_names = [a.team.team_name for a in ntourn.agents]
        assert "TestTeam1" in team_names
        assert "TestTeam2" in team_names
        assert len(a1.tournaments) == 1
        assert len(a2.tournaments) == 1


def test_add_teams_agents_tournament_match():
    """
    Add 2 teams to the db, an agent each,  and a tournament for them to play,
    containing one match
    """
    with test_session_scope() as tsession:
        t1 = Team()
        t1.team_name = "TestTeam1"
        t1.team_members = "Someone, something"
        t2 = Team()
        t2.team_name = "TestTeam2"
        t2.team_members = "Someone, something"
        a1 = Agent()
        a1.agent_name = "TestTeam1:panther_latest"
        a1.agent_type = "panther"
        a1.team = t1
        a2 = Agent()
        a2.agent_name = "TestTeam2:pelican_latest"
        a2.agent_type = "pelican"
        a2.team = t2
        tourn = Tournament()
        tourn.tournament_time = datetime.datetime.now()
        tourn.agents = [a1, a2]
        m = Match()
        m.match_time = datetime.datetime.now()
        m.game_config = "dummy"
        m.num_games = 10
        m.logfile_url = "dummy"
        m.pelican_agent = a1
        m.panther_agent = a2
        tourn.matches.append(m)
        tsession.add(t1)
        tsession.add(t2)
        tsession.add(a1)
        tsession.add(a2)
        tsession.add(tourn)
        tsession.add(m)
        tsession.commit()
        # now query the match table
        nm = tsession.query(Match).order_by(Match.match_id.desc()).first()
        assert isinstance(nm, Match)
        assert isinstance(nm.pelican_agent, Agent)
        assert isinstance(nm.panther_agent, Agent)
        assert isinstance(nm.pelican_agent.team, Team)
        assert isinstance(nm.panther_agent.team, Team)
        assert isinstance(nm.tournament, Tournament)
        # query the other way round
        nt = tsession.query(Team).order_by(Team.team_id.desc()).first()
        assert isinstance(nt, Team)
        assert len(nt.agents) == 1
        assert len(nt.agents[0].tournaments) == 1
        assert len(nt.agents[0].tournaments[0].matches) == 1


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
