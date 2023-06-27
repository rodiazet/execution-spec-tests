"""
A small pytest plugin that shows the a concise help string that only contains
the options defined by the plugins defined in execution-spec-tests (est).
"""

import argparse

import pytest


def pytest_addoption(parser):
    """
    Adds command-line options to pytest.
    """
    help_group = parser.getgroup(
        "est_help", "Arguments related to getting help for execution-spec-tests:"
    )
    help_group.addoption(
        "--eth-help",
        "--est-help",
        action="store_true",
        dest="show_est_help",
        default=False,
        help="Only show help options specific to execution-spec-tests and exit.",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """
    Print execution-spec-tests help if specified on the command-line.
    """
    if config.getoption("show_est_help"):
        show_est_help(config)
        pytest.exit("After displaying help.", returncode=pytest.ExitCode.NO_TESTS_COLLECTED)


def show_est_help(config):
    """
    Print the help for argparse groups that contain substrings indicating
    that group is specific to execution-spec-tests command-line
    arguments.
    """
    est_group_substrings = [
        "execution-spec-tests",
        "evm",
        "solc",
        "fork range",
        "filler location",
    ]

    est_parser = argparse.ArgumentParser()
    for group in config._parser.optparser._action_groups:
        if any(group for substring in est_group_substrings if substring in group.title):
            new_group = est_parser.add_argument_group(group.title, group.description)
            for action in group._group_actions:
                # Copy the option to the new group.
                # Works for 'store', 'store_true', and 'store_false'.
                kwargs = {
                    "default": action.default,
                    "type": action.type,
                    "help": action.help,
                }
                if action.nargs is not None and action.nargs != 0:
                    kwargs["nargs"] = action.nargs
                new_group.add_argument(*action.option_strings, **kwargs)
    print(est_parser.format_help())
