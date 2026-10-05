"""Live provider tests can never run accidentally; real media is a separate layer."""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Opt in to live-provider tests, which may consume paid credits",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--live"):
        skip = pytest.mark.skip(
            reason="Live providers require --live; calls may consume paid credits"
        )
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip)
