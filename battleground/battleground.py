"""
"""

import os
import numpy as np
import logging

import imageio
import PIL.Image

from classes.newgame import (
    Newgame,
    load_agent,
)
from classes.move import Move


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


VIDEO_BASE_WIDTH = 512
VIDEO_FPS = 1


class Battle(Newgame):
    """
    Battle class.

    """

    def __init__(self, game_config, **kwargs):
        """
        constructor

        Arguments:
            game_config -
            kwargs -
        """

        self.gamePlayerTurn = None

        # load the game configurations
        self.load_configurations(game_config, **kwargs)

        # Create required game objects
        self.create_game_objects()

        # Load agents

        relative_basic_agents_filepath = os.path.normpath(
            os.path.join(
                os.getenv("PLARKAICOMPS"),
                "plark-game",
                "plark_game",
                "agents",
                "basic",
            )
        )

        self.pelicanAgent = load_agent(
            self.pelican_parameters["agent_filepath"],
            self.pelican_parameters["agent_name"],
            relative_basic_agents_filepath,
            self,
        )

        self.pantherAgent = load_agent(
            self.panther_parameters["agent_filepath"],
            self.panther_parameters["agent_name"],
            relative_basic_agents_filepath,
            self,
        )

        self.gamePlayerTurn = "ALL"

        self.default_game_variables()

        # Create UI objects and render game.
        #   This must be the last thing in the __init__
        param_name = "render_height"
        if param_name in self.pelican_parameters.keys():
            setattr(self, param_name, self.pelican_parameters[param_name])
        elif param_name in self.panther_parameters.keys():
            setattr(self, param_name, self.pelican_parameters[param_name])
        else:
            setattr(self, param_name, 250)

        param_name = "render_width"
        if param_name in self.pelican_parameters.keys():
            setattr(self, param_name, self.pelican_parameters[param_name])
        elif param_name in self.panther_parameters.keys():
            setattr(self, param_name, self.pelican_parameters[param_name])
        else:
            setattr(self, param_name, 310)

        self.reset_game()

        self.render(self.render_width, self.render_height, self.gamePlayerTurn)

    def pelicanPhase(self):
        """
        Pelican's move
        """

        logger.info("Pelican's move")

        self.pelicanMove = Move()
        while True:
            pelican_action = self.pelicanAgent.getAction(
                self._state("PELICAN")
            )

            self.perform_pelican_action(pelican_action)

            if (
                self.pelican_move_in_turn
                >= self.pelican_parameters["move_limit"]
                or pelican_action == "end"
            ):
                break

    def pantherPhase(self):
        """
        Panther's move
        """

        logger.info("Panther's move")

        self.pantherMove = Move()
        while True:
            panther_action = self.pantherAgent.getAction(
                self._state("PANTHER")
            )

            self.perform_panther_action(panther_action)
            if (
                self.gameState == "ESCAPE"
                or self.panther_move_in_turn
                >= self.panther_parameters["move_limit"]
                or panther_action == "end"
            ):
                break

    def play(self, video_file_path=None):
        """
        Plays a battle.

        Arguments:
            video_file_path - full path to where the resulting
                video file should be saved. (optional)
        Returns:
            None
        """

        logger.info("Battle begins!")

        if video_file_path is not None:
            writer = imageio.get_writer(video_file_path, fps=VIDEO_FPS)
        else:
            writer = None

        while True:

            if writer is not None:
                image = self.render(
                    view="ALL",
                    render_width=self.render_width,
                    render_height=self.render_height,
                )

                wpercent = VIDEO_BASE_WIDTH / float(image.size[0])
                hsize = int((float(image.size[1]) * float(wpercent)))

                res_image = image.resize(
                    (VIDEO_BASE_WIDTH, hsize), PIL.Image.ANTIALIAS
                )

                writer.append_data(np.copy(np.array(res_image)))

            state, output = self.game_step(None)

            print("state: ", state)

            if state != "Running":
                break

        if writer is not None:
            writer.close()

        logger.info("Battle finished.")

        # Who won?

        return
