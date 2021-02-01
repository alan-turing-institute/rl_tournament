import os
import json
import logging

# from abc import abstractmethod

from classes.newgame import load_agent
from classes.pantherAgent_load_agent import Panther_Agent_Load_Agent
from classes.pelicanAgent_load_agent import Pelican_Agent_Load_Agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# class combatant_panther():
#     @abstractmethod
#     def __load_agent(self):
#         self.panther_agent = None

#     def __init__(self):
#         self.__load_agent()


def load_combatant(
    agent_path, agent_name, basic_agents_path, game=None, **kwargs
):
    """
    Loads agent as a combatant.
        agent_path:
        agent_name:
        basic_agents_path:
        game:
        kwargs:
    Returns:
        agent
    """

    if ".py" in agent_path:
        return load_agent(
            agent_path, agent_name, basic_agents_path, game, **kwargs
        )
    else:

        files = os.listdir(agent_path)

        for f in files:
            if ".zip" not in f:
                # ignore non agent files
                pass

            elif ".zip" in f:
                # load model
                metadata_filepath = os.path.join(agent_path, "metadata.json")
                agent_filepath = os.path.join(agent_path, f)

                with open(metadata_filepath) as f:
                    metadata = json.load(f)

                if (
                    "image_based" in metadata
                    and metadata["image_based"] is False
                ):
                    return load_agent(
                        agent_path,
                        agent_name,
                        basic_agents_path,
                        game,
                        **kwargs
                    )

                observation = None
                image_based = True
                algorithm = metadata["algorithm"]
                print("algorithm: ", algorithm)

                if metadata["agentplayer"] == "pelican":
                    return Pelican_Agent_Load_Agent(
                        agent_filepath,
                        algorithm,
                        observation,
                        image_based,
                    )
                elif metadata["agentplayer"] == "panther":
                    return Panther_Agent_Load_Agent(
                        agent_filepath,
                        algorithm,
                        observation,
                        image_based,
                    )

    return None
