"""
"""

import os
import requests

import subprocess

CONST_TEAMS_LIST = ["team1", "team2", "team3", "team4", "team5", "team_test"]
CONST_GITHUB_ADDRESS = (
    "https://raw.githubusercontent.com/"
    + "alan-turing-institute/rl_tournament/main/teams/"
)
CONST_TOURNAMENT_FILE = "/tmp/tournament.txt"


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

    tags = req.content.decode("UTF-8").split()

    return tags


def create_tournament():
    """
    Creates a tournament file.

    """

    tags = {}

    for team in CONST_TEAMS_LIST:
        tags[team] = get_team_repository_tags(team)

    f = open(CONST_TOURNAMENT_FILE, "w")

    for i in range(len(CONST_TEAMS_LIST) - 1):
        team_i = CONST_TEAMS_LIST[i]

        for j in range(i + 1, len(CONST_TEAMS_LIST)):
            team_j = CONST_TEAMS_LIST[j]

            for i_tag in tags[team_i]:
                for j_tag in tags[team_j]:

                    f.write("%s,%s,%s,%s\n" % (team_i, i_tag, team_j, j_tag))

    f.close()


def docker_compose():
    """"""

    cwd = os.getcwd()

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    os.chdir(path)

    print("BUILD")
    subprocess.run(["docker-compose", "build"])

    # print("UP")
    # cmd.up(options)

    # cmd.logs(options)

    # print("DOWN")
    # cmd.down(options)

    os.chdir(cwd)


if __name__ == "__main__":

    # create_tournament()

    docker_compose()

    print("Finished")
