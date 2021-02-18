"""
"""

import os
import subprocess
import requests
import logging
from datetime import date
import time

from battleground.azure_config import config as az_config
from battleground.azure_utils import list_directory
from battleground.db_utils import (
    create_db_team,
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
    participating_teams = [team.split(":")[0] for team in pelicans + panthers]
    participating_teams = list(set(participating_teams))
    for team in participating_teams:
        create_db_team(team, "members_placeholder")
    tournament_id = create_db_tournament(participating_teams)
    return tournament_id


def get_match_config_file():
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

    config_list = list_directory(path, container_name)

    if len(config_list) == 0:
        return config_file_name

    for config_file in config_list:
        if config_file.startswith(current_day):
            config_file_name = config_file
            break

    if config_file_name is None:

        for config_file in config_list:
            if config_file == CONST_DEFAULT_MATCH_CONFIG_FILE:
                config_file_name = config_file
                break

    logging.info("For %s will use %s" % (current_day, config_file_name))

    return config_file_name


def run_tournament(tournament_id):
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

    # get a match config file for the day
    config_file_name = get_match_config_file()

    if config_file_name is None:
        return False, "Could not find a match config file."

    no_matches = len(matches)
    logging.info("The tournament will have %d match(es)" % (no_matches))

    for match_idx, match in enumerate(matches):

        logging.info("Running match %d/%d" % (match_idx + 1, no_matches))

        match_yaml = template

        pelican, panther = match.split()

        pelican_team, pelican_image_tag = pelican.split(":")
        panther_team, panther_image_tag = panther.split(":")

        # register new match
        try:
            # create the match in the database
            match_id = create_db_match(
                pelican_team,
                pelican_image_tag,
                panther_team,
                panther_image_tag,
                game_config=config_file_name,
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
        subprocess.run(["docker-compose", "pull"])
        logging.info(
            "docker-compose pull took %d s." % (time.time() - docker_st)
        )

        docker_st = time.time()
        logging.info("docker-compose up")
        subprocess.Popen(["docker-compose", "up"])

        while (time.time() - docker_st) < 1800:
            if match_finished(match_id):
                logging.info("Match took %d s." % (time.time() - docker_st))
                break
            else:
                logging.info("Match is still running. Sleep(5)")
                time.sleep(5)

        logging.info("docker-compose down")
        docker_st = time.time()
        # subprocess.run(["docker-compose", "down"])
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

    tid = create_tournament()

    success, error = run_tournament(tid)

    clean_up()

    print(success, error)
