"""
"""

from tournament.tournament import get_match_config_file


def test_get_match_config_file():

    file = get_match_config_file()

    assert file is not None
