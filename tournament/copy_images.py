import os
import argparse
import logging
import requests
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
)

CONST_REGISTRY_SRC = "turingrldsg.azurecr.io"
CONST_TEAMS_LIST = [
    "team_1",
    "team_2",
    "team_3",
    "team_4",
    "team_5",
    "team_test",
]
CONST_GITHUB_ADDRESS = (
    "https://raw.githubusercontent.com/"
    + "alan-turing-institute/rl_tournament/main/teams/"
)


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


def login_src():

    # Logging in to the source repo
    command = [
        "docker",
        "login",
        CONST_REGISTRY_SRC,
        "-u",
        os.environ.get("RL_ADMIN_TOKEN_NAME"),
        "-p",
        os.environ.get("RL_ADMIN_TOKEN"),
    ]

    if not no_sudo:
        command = ["sudo"] + command
    subprocess.call(command)


def login_dst():
    registry_dst = os.environ.get("DEST_REPO")

    # Logging in to the destination repo
    command = [
        "docker",
        "login",
        registry_dst,
        "-u",
        os.environ.get("DEST_TOKEN_NAME"),
        "-p",
        os.environ.get("DEST_TOKEN"),
    ]

    if not no_sudo:
        command = ["sudo"] + command
    subprocess.call(command)


def main(no_sudo):

    login_src()
    login_dst()

    registry_dst = os.environ.get("DEST_REPO")

    logging.info("Copying images")

    for team in CONST_TEAMS_LIST:
        logging.info("  Team: %s" % (team))

        tags = get_team_repository_tags(team)

        logging.info("  Team: %s tags: %s" % (team, tags))

        for tag in tags:

            image_src = "%s/%s:%s" % (CONST_REGISTRY_SRC, team, tag)

            logging.info("docker pull %s" % (image_src))
            command = ["docker", "pull", image_src]
            if not no_sudo:
                command = ["sudo"] + command
            subprocess.call(command)

            image_dst = "%s/%s:%s" % (registry_dst, team, tag)

            logging.info("docker tag %s -> %s" % (image_src, image_dst))
            command = ["docker", "tag", image_src, image_dst]
            if not no_sudo:
                command = ["sudo"] + command
            subprocess.call(command)

            logging.info("docker push %s" % (image_dst))

            command = ["docker", "push", image_dst]
            if not no_sudo:
                command = ["sudo"] + command
            subprocess.call(command)

    logging.info("Finished")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="copy docker images to a new registry")

    parser.add_argument(
        "--no_sudo",
        help="no sudo",
        action="store_true",
    )

    args = parser.parse_args()

    no_sudo = args.no_sudo if args.no_sudo else False

    main(no_sudo)
