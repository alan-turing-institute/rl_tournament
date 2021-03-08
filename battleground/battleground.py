"""
Classes needed to run the Plark game with agents communicating via
RabbitMQ messages.
"""

import os
import json
import datetime
import numpy as np
import pika
import uuid
import time

from pika.adapters.utils.connection_workflow import (
    AMQPConnectorSocketConnectError,
)

import imageio
import PIL.Image

import logging
from logging.handlers import RotatingFileHandler

from plark_game.classes.newgamebase import NewgameBase
from plark_game.classes.move import Move
from plark_game.classes.observation import Observation

from battleground.serialization import serialize_state
from battleground.schema import Match, Game, session

from battleground.azure_utils import write_file_to_blob, read_json
from battleground.azure_config import config

# configure the logger
logger = logging.getLogger("battleground_logger")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
logger.setLevel(logging.INFO)
c_handler = logging.StreamHandler()
c_handler.setFormatter(formatter)

logger.addHandler(c_handler)

VIDEO_BASE_WIDTH = 512
VIDEO_FPS = 1


def make_az_url(storage_account_name, container_name, blob_name):
    """
    return the URL on Azure blob storage of a blob.
    """
    return "https://{}.blob.core.windows.net/{}/{}".format(
        storage_account_name, container_name, blob_name
    )


class Battleground():
    """
    Equivalent of 'Environment' class in plark_ai_public/Components/plark-game.
    Fulfils the same role - manages the creation and configuration of games.
    Only difference is that instead of creating 'Newgame' instances,
    we create 'Battle' instances.
    Also have code to create interact with the database, and to ensure
    that the RabbitMQ queue is up, and both agents have sent a "ready" message.
    """

    def __init__(self, match_id, dbsession=session, **kwargs):
        self.activeGames = []
        self.numberOfActiveGames = 0
        match_id = int(match_id)
        # new logfile name for this match
        self.f_handler = RotatingFileHandler(
            "match_{}_{}.log".format(
                match_id, time.strftime("%Y-%m-%d_%H-%M-%S")
            ),
            maxBytes=5 * 1024 * 1024,
            backupCount=10,
        )
        self.f_handler.setFormatter(formatter)
        logger.addHandler(self.f_handler)
        match = dbsession.query(Match).filter_by(match_id=match_id).first()
        if not match:
            raise RuntimeError(
                "Could not find match {} in DB".format(match_id)
            )
        self.match_id = match_id
        self.num_games = match.num_games
        self.config_file = match.game_config
        # see if we have established communication with the agents
        self.pelican_ready = False
        self.panther_ready = False

    def setup_games(self, **kwargs):
        """
        Create num_games Battle objects, with the chosen game_config
        """
        self.game_config = read_json(
            blob_name=self.config_file,
            container_name=config["config_container_name"],
        )
        # set a couple of parameters by hand to avoid problems
        self.game_config["render_settings"]["output_view_all"] = False
        self.game_config["game_settings"]["driving_agent"] = ""

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

    def listen_for_ready(self):
        """
        When they have started up, the agents will send a "ready"
        message to the queue 'rpc_queue_ready'.  Here we setup the
        queue to listen for those messages, and once connected to it,
        start listening.
        """

        ready_queue = "rpc_queue_ready"

        if "RABBITMQ_HOST" in os.environ.keys():
            hostname = os.environ["RABBITMQ_HOST"]
        else:
            hostname = "localhost"

        # wait for the RabbitMQ queue to become ready
        connected = False
        while not connected:
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=hostname,
                        heartbeat=600,
                        blocked_connection_timeout=300
                    )
                )
                connected = True
            except (
                pika.exceptions.AMQPConnectionError,
                AMQPConnectorSocketConnectError,
            ):
                logger.info("Waiting for connection...")
                time.sleep(2)
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue=ready_queue)
        self.channel.basic_qos(prefetch_count=1)

        self.channel.basic_consume(
            queue=ready_queue,
            on_message_callback=self.set_agent_ready,
            auto_ack=True,
        )
        logger.info("Listening for agents becoming ready.")
        self.channel.start_consuming()


    def set_agent_ready(self, ch, method, props, body):
        """
        If we receive a message saying "panther_ready" or "pelican_ready",
        set our flags accordingly, and reply with the correlation_id
        """
        print("got a message: {}".format(body))
        message = body.decode("utf-8")
        if message == "PANTHER_READY":
            self.panther_ready = True
        elif message == "PELICAN_READY":
            self.pelican_ready = True

        if self.pelican_ready and self.panther_ready:
            logger.info("Both agents ready, will start match")
            time.sleep(1)
            self.channel.stop_consuming()

    def play(self):
        print("In play - will do {} games".format(len(self.activeGames)))
        for i, game in enumerate(self.activeGames):
            video_filename = "match_{}_game_{}_{}.mp4".format(
                self.match_id, i, time.strftime("%Y-%m-%d_%H-%M-%S")
            )
            game.play(match_id=self.match_id, video_file_path=video_filename)
        self.save_logfile()

    def save_logfile(self):
        """
        Save the logfile to cloud storage, then update location in the
        database.
        """
        # save logfile to Cloud storage
        log_path = self.f_handler.baseFilename
        log_filename = os.path.basename(log_path)
        write_file_to_blob(
            log_path, log_filename, config["logfile_container_name"]
        )

        # retrieve the match from the db so we can update its logfile_url
        m = session.query(Match).filter_by(match_id=self.match_id).first()
        if not m:
            raise RuntimeError(
                "Unable to retrieve match {} from db".format(self.match_id)
            )
        logfile_url = make_az_url(
            config["storage_account_name"],
            config["logfile_container_name"],
            log_filename,
        )
        m.logfile_url = logfile_url
        session.add(m)
        session.commit()


class Battle(NewgameBase):
    """
    Battle class.  Derives from NewGameBase, but overrides the constructor,
    pantherPhase and pelicanPhase so that rather than owning the agents,
    the battle instance instead sends messages to them via RabbitMQ.

    """

    def __init__(self, game_config, **kwargs):
        """
        constructor

        Arguments:
            game_config -
            kwargs -
        """

        super().__init__(game_config, **kwargs)

        self.gamePlayerTurn = None

        # Initialize the RabbitMQ connection
        self.setup_message_queues()

        self.gamePlayerTurn = "ALL"

        self.default_game_variables()

        # create "Observation" objects for the two agents
        self.observation = {
            "PANTHER": Observation(self, driving_agent="panther"),
            "PELICAN": Observation(self, driving_agent="pelican"),
        }

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
        connected = False
        while not connected:
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=hostname,
                        heartbeat=600,
                        blocked_connection_timeout=300
                    )
                )
                connected = True
            except (
                pika.exceptions.AMQPConnectionError,
                AMQPConnectorSocketConnectError,
            ):
                logger.info("Waiting for connection...")
                time.sleep(2)
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
        obs = self.observation[agent_type].get_original_observation(game_state)
        obs_normalised = self.observation[
            agent_type
        ].get_normalised_observation(game_state)
        domain_parameters = self.observation[
            agent_type
        ].get_remaining_domain_parameters()
        domain_parameters_normalised = self.observation[
            agent_type
        ].get_normalised_remaining_domain_parameters()
        body = {
            "state": serialized_game_state,
            "obs": list(obs),
            "obs_normalised": list(obs_normalised),
            "domain_parameters": list(domain_parameters),
            "domain_parameters_normalised": list(domain_parameters_normalised),
        }
        self.response = None
        self.channel.basic_publish(
            exchange="",
            routing_key=self.routing_keys[agent_type],
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(body),
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

    def play(self, match_id=0, video_file_path=None, dbsession=session):
        """
        Plays a battle.

        Arguments:
            video_file_path - full path to where the resulting
                video file should be saved. (optional)
        Returns:
            None
        """

        logger.info("Battle begins!")
        parent_match = (
            dbsession.query(Match).filter_by(match_id=match_id).first()
        )
        if not parent_match:
            raise RuntimeError(
                "unable to find match with id {} in db".format(match_id)
            )

        g = Game()
        g.match = parent_match
        g.game_time = datetime.datetime.now()
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
        logger.info(
            "Saving video to {}/{}".format(
                config["video_container_name"],
                os.path.basename(video_file_path),
            )
        )
        video_filename = os.path.basename(video_file_path)
        write_file_to_blob(
            video_file_path, video_filename, config["video_container_name"]
        )
        logger.info("Battle finished.")
        video_url = make_az_url(
            config["storage_account_name"],
            config["video_container_name"],
            video_filename,
        )
        g.video_url = video_url

        dbsession.add(g)
        dbsession.commit()

        return
