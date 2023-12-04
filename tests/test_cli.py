import shlex
from pathlib import Path

from freakotp.cli import EXIT_PARSER_ERROR, EXIT_SUCCESS, main

DB_PATH = Path(__file__).parent / 'test.db'


def r(cmd: str, exp=EXIT_SUCCESS):
    prefix = f"freakotp --db {DB_PATH} "
    assert main(shlex.split(prefix + cmd)) == exp


def test_otp():
    r(".otp")
    r(".otp atom")
    r(".otp -l atom")
    r("-c 99 .otp")
    r("-c 99.otp", EXIT_PARSER_ERROR)


def test_ls():
    r(".ls")
    r(".ls -l")
    r(".ls -l atom")


def test_qrcode():
    r(".qrcode atom")


def test_uri():
    r(".qrcode atom")


def test_help():
    r(".help")
    r("--help")
    r("-h", EXIT_PARSER_ERROR)
