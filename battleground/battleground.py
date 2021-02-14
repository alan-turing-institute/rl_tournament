"""
Classes needed to run the Plark game with agents communicating via
RabbitMQ messages.
"""

import os
import json
import numpy as np
import pika
import uuid
import logging
import time

import imageio
import PIL.Image

import logging
from logging.handlers import RotatingFileHandler

from plark_game.classes.environment import Environment
from plark_game.classes.newgame import Newgame
from plark_game.classes.move import Move

from battleground.serialization import serialize_state
from battleground.schema import (
    Team,
    Match,
    Game,
    session
)

from battleground.azure_utils import write_file_to_blob, read_json

MATCH_ID = int(os.environ["MATCH_ID"]) if "MATCH_ID" in os.environ.keys() \
               else 0

# configure the logger
logger = logging.getLogger("battleground_logger")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
logger.setLevel(logging.INFO)
f_handler = RotatingFileHandler(
    "match_{}_{}.log".format(MATCH_ID, time.strftime("%Y-%m-%d_%H-%M-%S")),
    maxBytes=5 * 1024 * 1024, backupCount=10
)
f_handler.setFormatter(formatter)
c_handler = logging.StreamHandler()
c_handler.setFormatter(formatter)


logger.addHandler(f_handler)
logger.addHandler(c_handler)

VIDEO_BASE_WIDTH = 512
VIDEO_FPS = 1
CONFIG_CONTAINER_NAME = "config-files"
VIDEO_CONTAINER_NAME = "video-files"
LOGFILE_CONTAINER_NAME = "log-files"


class Battleground(Environment):
    """
    Derived class of 'Environment', fulfils the same role - manages the
    creation and configuration of games.   Only difference is that instead
    of creating 'Newgame' instances, we create 'Battle' instances.
    """

    def __init__(self, match_id, num_games, config_file, **kwargs):
        super().__init__(**kwargs)
        self.match_id = match_id
        self.num_games = num_games
        self.config_file = config_file


    def setup_games(self, **kwargs):

        self.game_config = read_json(
            blob_name=self.config_file,
            container_name=CONFIG_CONTAINER_NAME
        )

        logger.info("Loaded game config {}".format(self.config_file))
        for i in range(self.num_games):
            logger.info("Creating game {}".format(i))
            self.create_battle(**kwargs)


    # Triggers the creation of a new game
    def create_battle(self, **kwargs):

        gm = Battle(self.game_config, **kwargs)
        self.activeGames.append(gm)
        self.numberOfActiveGames = self.numberOfActiveGames + 1
        logger.info("Game Created")


    def play(self):
        for i, game in enumerate(self.activeGames):
            video_filename = "match_{}_game_{}_{}.mp4".\
                format(
                    self.match_id,
                    i,
                    time.strftime("%Y-%m-%d_%H-%M-%S")
                )
            game.play(match_id=self.match_id,
                      video_file_path=video_filename)
        self.save_logfile()

    def save_logfile(self):
        """
        Save the logfile to cloud storage, then update location in the
        database.
        """
        # save logfile to Cloud storage
        log_path = f_handler.baseFilename
        log_filename = os.path.basename(log_path)
        write_file_to_blob(log_path,
                           log_filename,
                           LOGFILE_CONTAINER_NAME)
        # retrieve the match from the db so we can update its logfile_url
        m = session.query(Match).filter_by(match_id=self.match_id).first()
        if not m:
            raise RuntimeError("Unable to retrieve match {} from db".format(self.match_id))
        m.logfile_url = log_filename
        session.add(m)
        session.commit()


class Battle(Newgame):
    """
    Battle class.  Derives from NewGame, but overrides the constructor,
    pantherPhase and pelicanPhase so that rather than owning the agents,
    the battle instance instead sends messages via RabbitMQ.

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

        # Initialize the RabbitMQ connection
        self.setup_message_queues()

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



    def setup_message_queues(self):
        if "RABBITMQ_HOST" in os.environ.keys():
            hostname = os.environ["RABBITMQ_HOST"]
        else:
            hostname = "localhost"
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=hostname)
        )

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )
        self.routing_keys = {
            "PELICAN": "rpc_queue_pelican",
            "PANTHER": "rpc_queue_panther",
        }

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def get_agent_action(self, agent_type):
        """
        Send a message to the appropriate queue to get
        an "action" from an agent.

        Parameters
        ==========
        agent_type: str, must be "PELICAN" or "PANTHER"

        Returns
        =======
        action: str, representation of an integer.
        """
        if agent_type not in ["PANTHER", "PELICAN"]:
            raise RuntimeError(
                "Unknown agent type {}, must be PANTHER or PELICAN".format(
                    agent_type
                )
            )
        # generate a uuid to identify this message
        self.corr_id = str(uuid.uuid4())
        # get the game state from the point-of-view of this agent
        game_state = self._state(agent_type)
        serialized_game_state = serialize_state(game_state)
        self.response = None
        self.channel.basic_publish(
            exchange="",
            routing_key=self.routing_keys[agent_type],
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(serialized_game_state),
        )
        while self.response is None:
            self.connection.process_data_events()
        return self.response.decode("utf-8")

    def pelicanPhase(self):
        """
        Pelican's move
        """

        logger.info("Pelican's move")

        self.pelicanMove = Move()
        while True:
            pelican_action = self.get_agent_action("PELICAN")
            logger.info("pelican action {}".format(pelican_action))
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
            panther_action = self.get_agent_action("PANTHER")
            logger.info("panther action {}".format(panther_action))
            self.perform_panther_action(panther_action)
            if (
                self.gameState == "ESCAPE"
                or self.panther_move_in_turn
                >= self.panther_parameters["move_limit"]
                or panther_action == "end"
            ):
                break

    def play(self, match_id=0, video_file_path=None):
        """
        Plays a battle.

        Arguments:
            video_file_path - full path to where the resulting
                video file should be saved. (optional)
        Returns:
            None
        """

        logger.info("Battle begins!")
        parent_match = session.query(Match).filter_by(match_id=match_id).first()
        if not parent_match:
            raise RuntimeError("unable to find match with id {} in db".format(match_id))

        g = Game()
        g.match = parent_match


        if video_file_path is not None:
            writer = imageio.get_writer(video_file_path, fps=VIDEO_FPS)
        else:
            writer = None
        num_turns = 0
        state = None
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
            num_turns += 1

        g.num_turns = num_turns
        g.result_code = state
        if writer is not None:
            writer.close()
        logger.info("Saving video to {}/{}".format(
            VIDEO_CONTAINER_NAME,
            os.path.basename(video_file_path)
        ))
        write_file_to_blob(
            video_file_path,
            os.path.basename(video_file_path),
            VIDEO_CONTAINER_NAME
        )
        logger.info("Battle finished.")

        # Who won?

        return
