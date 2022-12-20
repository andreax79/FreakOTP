from pathlib import Path
import shlex
from freakotp.cli import main, EXIT_SUCCESS, EXIT_PARSER_ERROR

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
