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

Other python dependencies are listed in `requirements.txt`