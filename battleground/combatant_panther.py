"""
Script to run a Pelican agent and listen for messages from the Game.

Before running, set environment variable PLARKAICOMPS to point to the
  plark_ai_public/  directory
"""

import os
import json
import logging
import pika

from combatant import Combatant

logging.basicConfig()


def run_panther(agent_path, agent_name, basic_agents_path):
    panther_agent = Combatant(agent_path, agent_name, basic_agents_path)
    if "RABBITMQ_HOST" in os.environ.keys():
        hostname = os.environ["RABBITMQ_HOST"]
    else:
        hostname = "localhost"
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=hostname)
    )

    channel = connection.channel()

    channel.queue_declare(queue="rpc_queue_panther")
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue="rpc_queue_panther", on_message_callback=panther_agent.get_action
    )

    print(" [x] PANTHER Awaiting RPC requests")
    channel.start_consuming()


if __name__ == "__main__":

    if "PLARKAICOMPS" not in os.environ.keys():
        raise RuntimeError(
            """
            Please set environment var PLARKAICOMPS to point
            to the plark_ai_public/ directory
            """
        )

    config_file = "tests/test_configs/10x10_balanced.json"
    if not os.path.exists(config_file):
        raise RuntimeError("Unable to find config {}".format(config_file))
    config = json.load(open(config_file))
    agent_path = config["game_rules"]["panther"]["agent_filepath"]
    agent_name = config["game_rules"]["panther"]["agent_name"]
    basic_agents_path = os.path.normpath(
        os.path.join(
            os.getenv("PLARKAICOMPS"),
            "plark-game",
            "plark_game",
            "agents",
            "basic",
        )
    )
    run_panther(agent_path, agent_name, basic_agents_path)
