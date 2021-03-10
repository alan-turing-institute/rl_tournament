"""
"""

import os
import subprocess
import requests
import argparse
import logging
from datetime import date, datetime
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

CONST_DEFAULT_MAP_SIZE = "10x10"


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


def create_tournament(test_run=False, map_size=CONST_DEFAULT_MAP_SIZE):
    """
    Creates a tournament file.

    """

    if map_size == CONST_DEFAULT_MAP_SIZE:
        small_tournament = True
    else:
        small_tournament = False

    logging.info("Preparing for the tournament")

    pelicans = []
    panthers = []

    logging.info("No of teams participating: %d" % len(CONST_TEAMS_LIST))

    for team in CONST_TEAMS_LIST:
        tags = get_team_repository_tags(team)
        if len(tags) > 0:
            for tag in tags:

                # - all agents go in the small tournament
                # - agents with "10x10" in the tag go in the 10x10 tournament
                #   but not the big grid one.
                if not small_tournament and CONST_DEFAULT_MAP_SIZE in tag:
                    add = False
                else:
                    add = True

                if add:
                    if "pelican" in tag:
                        pelicans.append("%s:%s" % (team, tag))
                    elif "panther" in tag:
                        panthers.append("%s:%s" % (team, tag))

    pelicans = list(set(pelicans))
    panthers = list(set(panthers))

    logging.info("No of PELICANS participating: %d" % len(pelicans))
    logging.info("No of PANTHERS participating: %d" % len(panthers))

    f = open(CONST_TOURNAMENT_FILE, "w")

    if test_run:
        pel_size = len(pelicans)
        pan_size = len(panthers)

        max_size = max(pel_size, pan_size)

        for i in range(max_size):
            if i < pel_size:
                pelican = pelicans[i]
            else:
                pelican = pelicans[pel_size - 1]

            if i < pan_size:
                panther = panthers[i]
            else:
                panther = panthers[pan_size - 1]

            f.write("%s %s\n" % (pelican, panther))

    else:
        for pelican in pelicans:
            for panther in panthers:
                # don't let agents from the same team play each other
                if pelican.split(":")[0] != panther.split(":")[0]:
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


def get_match_config_file(map_size=CONST_DEFAULT_MAP_SIZE, day=None):
    """
    Looks for a config file depending on the curent day. If a match file
        for the current day cannot be found, a default will be used.

    Returns:
        a list of files in the matches container
    """

    config_file_name = None

    if day is None:
        current_day = date.today().strftime("%Y_%m_%d")
    else:
        current_day = day

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
    tournament_id,
    num_games_per_match=10,
    map_size=CONST_DEFAULT_MAP_SIZE,
    day=None,
    no_sudo=False,
    test_run=False,
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
        config_file_name = get_match_config_file(map_size=map_size, day=day)

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

        if test_run:
            time_limit = 120
        else:
            time_limit = 1800

        while (time.time() - docker_st) < time_limit:
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
        time.sleep(3)
        # run this again, to make sure we remove the network
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
        default=CONST_DEFAULT_MAP_SIZE,
    )

    parser.add_argument(
        "--day",
        help="tournament day, format YYYY-MM-DD",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.now().strftime("%Y-%m-%d"),
    )

    parser.add_argument(
        "--tournament_id",
        help="""
        To retry a tournament, specify its ID here.
        Note that to only retry the last part of a tournament,
        you should edit /tmp/tournament.txt to only contain the
        matches you want to run.
        """,
        type=int,
    )

    parser.add_argument(
        "--test_run",
        help="Tournament test run",
        action="store_true",
    )

    args = parser.parse_args()

    no_sudo = args.no_sudo if args.no_sudo else False
    num_games_per_match = args.num_games_per_match
    map_size = args.map_size
    tour_day = args.day.strftime("%Y_%m_%d")
    test_run = args.test_run

    if test_run:
        num_games_per_match = 1

    # If we already have a tournament_id (i.e. we're retrying one)
    # Note that this will use /tmp/tournament.txt - this needs to
    # be edited if we only want to run e.g. the last part of a tournament
    if args.tournament_id:
        tid = args.tournament_id
    else:
        # create a new tournament using CONST_TEAMS_LIST and the txt files
        # in the repo, in the normal way
        tid = create_tournament(test_run=test_run, map_size=map_size)

    success, error = run_tournament(
        tid,
        num_games_per_match=num_games_per_match,
        map_size=map_size,
        day=tour_day,
        no_sudo=no_sudo,
        test_run=test_run,
    )

    clean_up()

    print(success, error)
