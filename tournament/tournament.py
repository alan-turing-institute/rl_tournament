"""
"""

import os
import subprocess
import requests
import argparse
import logging
from datetime import date
import time
import random

from battleground.azure_config import config as az_config
from battleground.azure_utils import list_directory
from battleground.db_utils import (
    create_db_agent,
    create_db_tournament,
    create_db_match,
    match_finished,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
)

# CONST_TEAMS_LIST = ["team_1",
# "team_2", "team_3", "team_4", "team_5", "team_test"]
CONST_TEAMS_LIST = ["team_test"]
CONST_GITHUB_ADDRESS = (
    "https://raw.githubusercontent.com/"
    + "alan-turing-institute/rl_tournament/main/teams/"
)
CONST_DOCKER_COMPOSE_TEMPLATE = "docker-compose-template.yml"
CONST_TOURNAMENT_FILE = "/tmp/tournament.txt"
CONST_TEMP_DOCKER_COMPOSE = "/tmp/docker-compose.yml"
CONST_DEFAULT_MATCH_CONFIG_FILE = "10x10_balanced.json"


def get_team_repository_tags(team_name):
    """
    Get the list tags (agents) for a team

    Arguments:
        team_name - team's name

    Returns:
        tags - a list of tags
    """

    address = "%s%s.txt" % (CONST_GITHUB_ADDRESS, team_name)

    req = requests.get(address)

    tags = req.content.decode("UTF-8").lower().split()

    return tags


def create_tournament():
    """
    Creates a tournament file.

    """

    logging.info("Preparing for the tournament")

    pelicans = []
    panthers = []

    logging.info("No of teams participating: %d" % len(CONST_TEAMS_LIST))

    for team in CONST_TEAMS_LIST:
        tags = get_team_repository_tags(team)
        if len(tags) > 0:
            for tag in tags:
                if "pelican" in tag:
                    pelicans.append("%s:%s" % (team, tag))
                elif "panther" in tag:
                    panthers.append("%s:%s" % (team, tag))

    pelicans = list(set(pelicans))
    panthers = list(set(panthers))

    logging.info("No of PELICANS participating: %d" % len(pelicans))
    logging.info("No of PANTHERS participating: %d" % len(panthers))

    f = open(CONST_TOURNAMENT_FILE, "w")

    for pelican in pelicans:
        for panther in panthers:

            f.write("%s %s\n" % (pelican, panther))

    f.close()

    logging.info(
        "Tournament file %s has been created." % (CONST_TOURNAMENT_FILE)
    )
    # add the teams and tournament to the database

    for agent in pelicans:
        create_db_agent(agent, "pelican")
    for agent in panthers:
        create_db_agent(agent, "panther")
    tournament_id = create_db_tournament(pelicans + panthers)
    return tournament_id


def get_match_config_file(map_size="25x25"):
    """
    Looks for a config file depending on the curent day. If a match file
        for the current day cannot be found, a default will be used.

    Returns:
        a list of files in the matches container
    """

    config_file_name = None

    current_day = date.today().strftime("%Y_%m_%d")

    logging.info("Looking for a config file for: %s" % (current_day))

    path = ""
    container_name = az_config["config_container_name"]

    configs_list = list_directory(path, container_name)

    if len(configs_list) == 0:
        logging.info("Could not find any configurations.")
        return config_file_name

    logging.info("Total number of configs: %d" % (len(configs_list)))

    sel_configs = []

    for config_file in configs_list:
        if config_file.startswith(current_day) and map_size in config_file:
            sel_configs.append(config_file)

    logging.info(
        "Total number of configs (%s) for the day: %d"
        % (map_size, len(sel_configs))
    )

    if len(sel_configs) == 0:
        logging.info(
            "Could not find any %s " % (map_size)
            + "configuration for today. Using default ones."
        )

        for config_file in configs_list:
            if config_file.startswith("default") and map_size in config_file:
                sel_configs.append(config_file)

        logging.info(
            "Total number of default %s configs: %d"
            % (map_size, len(sel_configs))
        )

    if len(sel_configs) == 0:
        logging.info(
            "Could not find a list of default configurations, will use: %s"
            % (CONST_DEFAULT_MATCH_CONFIG_FILE)
        )

        for config_file in configs_list:
            if config_file == CONST_DEFAULT_MATCH_CONFIG_FILE:
                config_file_name = config_file
                break
    else:
        config_file_name = random.choice(sel_configs)

    logging.info("For %s will use %s" % (current_day, config_file_name))

    return config_file_name


def run_tournament(
    tournament_id, num_games_per_match=10, map_size="25x25", no_sudo=False
):
    """
    Runs the tournament by running multiple docker-compose files

    Returns:
        success - flag whether the tournament was executed successfully
        error - error message, if any
    """

    success = True
    error = ""

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    template_path = os.path.join(path, CONST_DOCKER_COMPOSE_TEMPLATE)

    with open(template_path, "r") as file:
        template = file.read()

    with open(CONST_TOURNAMENT_FILE, "r") as file:
        matches = file.read().splitlines()

    no_matches = len(matches)
    logging.info("The tournament will have %d match(es)" % (no_matches))

    for match_idx, match in enumerate(matches):

        # get a match config file for the day
        config_file_name = get_match_config_file(map_size=map_size)

        if config_file_name is None:
            print("Could not find a match config file.")
            break

        logging.info("Running match %d/%d" % (match_idx + 1, no_matches))

        match_yaml = template

        pelican, panther = match.split()

        # register new match
        try:
            # create the match in the database
            match_id = create_db_match(
                pelican,
                panther,
                game_config=config_file_name,
                num_games=num_games_per_match,
                tournament_id=tournament_id,
            )

        except RuntimeError:
            match_id = None

        if match_id is None:
            error += "%s - %s resulted into an error: %s" % (
                pelican,
                panther,
                "cannot obtain match_id",
            )
            success = False
            break

        logging.info("match_id: %d" % (match_id))

        # prepare yaml file
        match_yaml = match_yaml.replace("<<PELICAN>>", pelican)
        match_yaml = match_yaml.replace("<<PANTHER>>", panther)
        match_yaml = match_yaml.replace("<<MATCH_ID>>", str(match_id))

        logging.info(
            "writing docker-compose file: %s", CONST_TEMP_DOCKER_COMPOSE
        )
        # write docker-compose
        with open(CONST_TEMP_DOCKER_COMPOSE, "w") as file:
            file.write(match_yaml)

        cwd = os.getcwd()

        logging.info("chdir /tmp")
        os.chdir("/tmp")

        logging.info("docker-compose pull")
        docker_st = time.time()
        command = ["docker-compose", "pull"]
        if not no_sudo:
            command = ["sudo"] + command
        subprocess.run(command)
        logging.info(
            "docker-compose pull took %d s." % (time.time() - docker_st)
        )

        docker_st = time.time()
        logging.info("docker-compose up")
        command = ["docker-compose", "up"]
        if not no_sudo:
            command = ["sudo"] + command
        subprocess.Popen(command)

        while (time.time() - docker_st) < 1800:
            if match_finished(match_id):
                logging.info("Match took %d s." % (time.time() - docker_st))
                break
            else:
                logging.info("Match is still running. Sleep(5)")
                time.sleep(5)

        logging.info("docker-compose down")
        docker_st = time.time()
        command = ["docker-compose", "down"]
        if not no_sudo:
            command = ["sudo"] + command
        subprocess.run(command)
        logging.info(
            "docker-compose down took %d s." % (time.time() - docker_st)
        )

        logging.info("chdir %s", cwd)
        os.chdir(cwd)

    return success, error


def clean_up():
    """
    Clean up after the tournament
    """

    os.remove(CONST_TOURNAMENT_FILE)

    try:
        os.remove(CONST_TEMP_DOCKER_COMPOSE)
    except FileNotFoundError:
        print("no need to delete %s" % (CONST_TEMP_DOCKER_COMPOSE))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="run a Plark tournament")
    parser.add_argument(
        "--no_sudo",
        help="""
                        For running on local machine,
                        don't use sudo for docker commands.
                        """,
        action="store_true",
    )
    parser.add_argument(
        "--num_games_per_match",
        help="number of games per match",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--map_size",
        help="map size",
        type=str,
        default="25x25",
        choices=["10x10", "25x25"],
    )
    args = parser.parse_args()

    no_sudo = args.no_sudo if args.no_sudo else False
    num_games_per_match = args.num_games_per_match
    map_size = args.map_size

    tid = create_tournament()

    success, error = run_tournament(
        tid, num_games_per_match, map_size, no_sudo
    )

    clean_up()

    print(success, error)
