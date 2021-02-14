"""
Database schema for RL tournament
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager

from .db_config import DB_CONNECTION_STRING

Base = declarative_base()


win_codes = {
    "BINGO" : "panther", # Pelican has run out of fuel, needs to return
    "WINCHESTER": "panther", # Pelican has no more torpedos
    "ESCAPE": "panther", # Panther has escaped
    "PELICANWIN": "pelican", # Pelican destroyed Panther
}

class Team(Base):
    __tablename__ = "team"
    team_id = Column(Integer, primary_key=True, nullable=False,
                      autoincrement=True)
    team_name = Column(String(100), nullable=False)
    team_members = Column(String(1000), nullable=False)
    matches = relationship("Match", uselist=True,
                           primaryjoin="or_(Team.team_id==Match.pelican_team_id, Team.team_id==Match.panther_team_id)")


class Match(Base):
    __tablename__ = "match"
    match_id = Column(Integer, primary_key=True, nullable=False,
                      autoincrement=True)
    match_time = Column(DateTime, nullable=False)
    pelican_team_id = Column(Integer, ForeignKey("team.team_id"))
    pelican_team = relationship("Team", back_populates="matches", foreign_keys=[pelican_team_id])
    # docker image name and tag
    pelican_agent = Column(String(100), nullable=False)
    panther_team_id = Column(Integer, ForeignKey("team.team_id"))
    panther_team = relationship("Team", back_populates="matches", foreign_keys=[panther_team_id])
    # docker image name and tag
    panther_agent = Column(String(100), nullable=False)
    # link to game config json (on cloud storage)
    game_config = Column(String(100), nullable=False)
    # link to logfile (on cloud storage)
    logfile_url = Column(String(100), nullable=False)
    games = relationship("Game", uselist=True,
                         back_populates="match")
    def winner(self):
        n_wins_pelican = 0
        n_wins_panther = 0
        n_draws = 0
        for game in self.games:
            if game.winner() == "pelican":
                n_wins_pelican += 1
            elif game.winner() == "panther":
                n_wins_panther += 1
            else:
                n_draws += 1
        if n_wins_pelican > n_wins_panther:
            return "pelican"
        elif n_wins_panther > n_wins_pelican:
            return "panther"
        else:
            return "draw"


class Game(Base):
    __tablename__ = "game"
    game_id = Column(Integer, primary_key=True, nullable=False,
                     autoincrement=True)
    num_turns = Column(Integer, nullable=False)
    result_code = Column(String(100), nullable=False)
    # link to video (on cloud storage)
    video_url = Column(String(100), nullable=False)
    match = relationship("Match", back_populates="games")
    match_id = Column(Integer, ForeignKey("match.match_id"))
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
