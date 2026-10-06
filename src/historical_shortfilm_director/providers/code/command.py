"""`scripts/code_video.py <action> ...` runs `hsd code <action> ...` from an uninstalled checkout."""

import sys

from historical_shortfilm_director.cli import main as cli_main


def main():
    return cli_main(["code", *sys.argv[1:]])
