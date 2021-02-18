## Developers guide for the rl_tournament package

This repository contains code to allow reinforcement learning agents to run the "Hunting the Plark" game in a tournament environment.
The game itself, and associated classes and configurations are in the repository
https://github.com/montvieux/plark_ai_public
This repository extends that code by:
* Adding a new `Battle` class that extends `Newgame`, and allows agent-vs-agent play with optional output to a video file.
* Adding `Combatant_Pelican` and `Combatant_Panther` classes that act as wrappers for the agents, and handle communication with the Battle instance.
* Communication is done via RabbitMQ messages - the Battle sends a JSON representation of the game state, and the agents reply with a string representation of their chosen action.
* Docker containers for the Battleground and Combatants are run together using `docker-compose`.
* SQL database and SQLAlchemy ORM keeps track of Teams, Matches, and individual Games.
* Logfiles and video files are stored on Azure blob storage (and URLs for them are stored in the database).


## Prerequisites

You need Docker and docker-compose to run the tournament.  See [here](https://docs.docker.com/engine/install/) for instructions on installing them.

You will also need to be able to run a recent python version (at least 3.6) locally.  Python dependencies are listed in `requirements.txt`.

### Setting environment variables

Copy the file `.env_template` to `.env` and fill in the various fields.  These are divided into database-related variables and Azure-storage-related variables.  See [here](database.md) for guidance on the database ones, and [here](azure-storage.md) for guidance on the Azure storage ones.

## Running a game

To run an example test game, with made-up teams, then assuming the fields in `.env` are set correctly, you can do
```
python create_match.py
```
this will add some teams and a match to the database, and create a file `docker-compose-match1.yml`.
You can then do
```
docker-compose -f docker-compose-match1.yml build
docker-compose -f docker-compose-match1.yml up
```
The first step will build the docker images.   The second will start them up, and run a match (consisting of 10 games, with the `10x10_balanced.json` config, and some default agents).
When the match is completed, you can do
```
docker-compose -f docker-compose-match1.yml down
```
to cleanly shut down the docker containers.
