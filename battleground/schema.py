"""
Database schema for RL tournament.

Basic idea:

* A TEAM is a team of participants in the challenge.
The corresponding table has columns for Team Name,
and Team Members.
Each TEAM will participate in one or more TOURNAMENTS.
* A TOURNAMENT will take place every day in the challenge.  All TEAMs that
take part in the TOURNAMENT will pit their agents against those of all the
other teams.  Each of these contests is a MATCH.
* A MATCH is a contest between a "Pelican" agent from one team, and a
"Panther" agent from another team. It will consist of multiple GAMES.
The winner of the MATCH is the TEAM whose agent won the most GAMES.
* A GAME is an individual round of the Plark game.  It will finish when
the Panther escapes, or the Pelican runs out of torpedos, or when the
Pelican destroys the Panther.

"""

from sqlalchemy import Table, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


from .db_config import DB_CONNECTION_STRING

Base = declarative_base()


win_codes = {
    "BINGO": "panther",  # Pelican has run out of fuel, needs to return
    "WINCHESTER": "panther",  # Pelican has no more torpedos
    "ESCAPE": "panther",  # Panther has escaped
    "PELICANWIN": "pelican",  # Pelican destroyed Panther
}

assoc_table = Table(
    "association",
    Base.metadata,
    Column("agent_id", Integer, ForeignKey("agent.agent_id")),
    Column("tournament_id", Integer, ForeignKey("tournament.tournament_id")),
)


class Team(Base):
    __tablename__ = "team"
    team_id = Column(
        Integer, primary_key=True, nullable=False, autoincrement=True
    )
    team_name = Column(String(100), nullable=False)
    team_members = Column(String(1000), nullable=False)
    agents = relationship("Agent", uselist=True, back_populates="team")


class Agent(Base):
    __tablename__ = "agent"
    agent_id = Column(
        Integer, primary_key=True, nullable=False, autoincrement=True
    )
    agent_name = Column(String(100), nullable=False)
    agent_type = Column(String(100), nullable=False)
    team = relationship("Team", back_populates="agents")
    team_id = Column(Integer, ForeignKey("team.team_id"))
    tournaments = relationship(
        "Tournament",
        uselist=True,
        back_populates="agents",
        secondary=assoc_table,
    )
    join_condition = "or_("
    join_condition += "Agent.agent_id==Match.pelican_agent_id"
    join_condition += ","
    join_condition += "Agent.agent_id==Match.panther_agent_id"
    join_condition += ")"
    matches = relationship(
        "Match",
        uselist=True,
        primaryjoin=join_condition,
    )


class Tournament(Base):
    __tablename__ = "tournament"
    tournament_id = Column(
        Integer, primary_key=True, nullable=False, autoincrement=True
    )
    tournament_time = Column(DateTime, nullable=False)
    agents = relationship(
        "Agent",
        uselist=True,
        back_populates="tournaments",
        secondary=assoc_table,
    )
    matches = relationship("Match", uselist=True, back_populates="tournament")


class Match(Base):
    __tablename__ = "match"
    match_id = Column(
        Integer, primary_key=True, nullable=False, autoincrement=True
    )
    match_time = Column(DateTime, nullable=False)
    tournament_id = Column(Integer, ForeignKey("tournament.tournament_id"))
    tournament = relationship(
        "Tournament", back_populates="matches", foreign_keys=[tournament_id]
    )

    pelican_agent_id = Column(Integer, ForeignKey("agent.agent_id"))
    pelican_agent = relationship(
        "Agent", back_populates="matches", foreign_keys=[pelican_agent_id]
    )
    panther_agent_id = Column(Integer, ForeignKey("agent.agent_id"))
    panther_agent = relationship(
        "Agent", back_populates="matches", foreign_keys=[panther_agent_id]
    )
    num_games = Column(Integer, nullable=False)
    # link to game config json (on cloud storage)
    game_config = Column(String(100), nullable=False)
    # link to logfile (on cloud storage)
    logfile_url = Column(String(100), nullable=False)
    games = relationship("Game", uselist=True, back_populates="match")

    def score(self, pelican_or_panther):
        if pelican_or_panther not in ["pelican", "panther"]:
            raise RuntimeError(
                """
                pelican_or_panther must be 'pelican' or 'panther', not {}
                """.format(
                    pelican_or_panther
                )
            )
        n_wins = 0
        for game in self.games:
            if game.winner == pelican_or_panther:
                n_wins += 1
        return n_wins

    @property
    def pelican_score(self):
        return self.score("pelican")

    @property
    def panther_score(self):
        return self.score("panther")

    @property
    def winner(self):
        if self.pelican_score > self.panther_score:
            return "pelican"
        elif self.panther_score > self.pelican_score:
            return "panther"
        else:
            return "draw"

    @property
    def winning_agent(self):
        if not self.is_finished:
            return None
        if self.winner == "pelican":
            return self.pelican_agent
        elif self.winner == "panther":
            return self.panther_agent
        else:
            return None

    @property
    def is_finished(self):
        if len(self.games) == self.num_games:
            return True
        else:
            return False


class Game(Base):
    __tablename__ = "game"
    game_id = Column(
        Integer, primary_key=True, nullable=False, autoincrement=True
    )
    game_time = Column(DateTime, nullable=False)
    num_turns = Column(Integer, nullable=False)
    result_code = Column(String(100), nullable=False)
    # link to video (on cloud storage)
    video_url = Column(String(100), nullable=False)
    match = relationship("Match", back_populates="games")
    match_id = Column(Integer, ForeignKey("match.match_id"))

    @property
    def winner(self):
        # look up based on result code
        return win_codes[self.result_code]


engine = create_engine(DB_CONNECTION_STRING)

Base.metadata.create_all(engine)
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine, autoflush=False)
# global database session used by default throughout the package
session = DBSession()
