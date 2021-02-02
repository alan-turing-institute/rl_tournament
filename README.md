# Reinforcement Learning Tournament

This repository contains code to allow reinforcement learning agents to run the "Hunting the Plark" game in a tournament environment.
The game itself, and associated classes and configurations are in the repository
https://github.com/montvieux/plark_ai_public
This repository extends that code by:
* Adding a new `Battle` class that extends `Newgame`, and allows agent-vs-agent play with optional output to a video file.
* Adding `Combatant_Pelican` and `Combatant_Panther` classes that act as wrappers for the agents, and handle communication with the Battle instance.
* Communication is done via RabbitMQ messages - the Battle sends a JSON representation of the game state, and the agents reply with a string representation of their chosen action.


## Prerequisites

Clone the `plark_ai_public` repository, change to the ```Components/plark-game/``` directory, and do
```
pip install .
```

Other python dependencies are listed in `requirements.txt`.

Docker is the easiest way to run RabbitMQ on your local machine.

## Running a game

To use some example pre-trained agents, edit the path in ```tests/test_configs/10x10_balanced.json``` so that the "agent_filepath"s point to the equivalents in your locally checked-out version of `plark_ai_public` (note that you will need to use `git-lfs` to download these large files from that repository). 

You can then do (in one terminal):
```
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
to start RabbitMQ.

In another terminal, run (from this directory):
```
export PLARKAICOMPS=/path/to/plark_ai_public
python battleground/combatant_panther.py
```

From another terminal, run (also from this directory):
```
export PLARKAICOMPS=/path/to/plark_ai_public
python battleground/combatant_pelican.py
```

And finally, from yet another terminal in this directory, start python
```
python
>>> from battleground.battleground import Battleground, Battle
>>> config_file_path = "tests/test_configs/10x10_balanced.json"
>>> bg = Battleground()
>>> bg.create_battle(config_file_path)
>>> battle = bg.activeGames[0]
>>> battle.play()
```

