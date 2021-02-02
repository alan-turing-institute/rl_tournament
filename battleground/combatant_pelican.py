"""
Script to run a Pelican agent and listen for messages from the Game.

Before running, set environment variable PLARKAICOMPS to point to the
  plark_ai_public/  directory
"""

import os
import json
import logging
logging.basicConfig()

import pika

from plark_game.classes.newgame import load_agent
from combatant import Combatant




def run_pelican(agent_path, agent_name, basic_agents_path):
    pelican_agent = Combatant(agent_path, agent_name, basic_agents_path)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )

    channel = connection.channel()

    channel.queue_declare(queue='rpc_queue_pelican')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='rpc_queue_pelican',
                          on_message_callback=pelican_agent.get_action)

    print(" [x] PELICAN Awaiting RPC requests")
    channel.start_consuming()


if __name__ == "__main__":
    config_file = "tests/test_configs/10x10_balanced.json"
    config = json.load(open(config_file))
    agent_path = config["game_rules"]["pelican"]["agent_filepath"]
    agent_name = config["game_rules"]["pelican"]["agent_name"]
    basic_agents_path = os.path.normpath(
        os.path.join(
            os.getenv("PLARKAICOMPS"),
            "plark-game",
            "plark_game",
            "agents",
            "basic"
            )
    )
    run_pelican(agent_path, agent_name, basic_agents_path)
