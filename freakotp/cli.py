#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2019 Andrea Bonomi <andrea.bonomi@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from datetime import datetime
import click
from click.utils import make_str
from click.core import Command, Context
from click.formatting import HelpFormatter
from pathlib import Path
from typing import List, Optional, Tuple
import appdirs
import pzp
from .secret import Secret
from .token import Token, TokenDb, TokenType, ALGORITHMS, DEFAULT_PERIOD, DEFAULT_ALGORITHM, DEFAULT_DIGITS

__author__ = "Andrea Bonomi <andrea.bonomi@gmail.com>"
__version__ = "3.0.1"
__all__ = [
    "main",
    "FreakOTP",
    "Token",
    "DEFAULT_PERIOD",
    "DEFAULT_ALGORITHM",
    "DEFAULT_DIGITS",
]

DESCRIPTION = "FreakOTP is a command line two-factor authentication application."
CONFIG_DIR = Path(appdirs.user_config_dir(appname="FreakOTP"))
DEFAULT_DB = CONFIG_DIR / "freakotp.db"

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_PARSER_ERROR = 2


class FreakOTPGroup(click.Group):
    def resolve_command(self, ctx: Context, args: List[str]) -> Tuple[Optional[str], Optional[Command], List[str]]:
        is_cmd = args and make_str(args[0]).startswith(".")
        if is_cmd:
            return super().resolve_command(ctx, args)
        else:
            return ".default", self.get_command(ctx, ".default"), args

    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        formatter.write_usage(ctx.command_path, "[OPTIONS] [COMMAND|[TOKENS]...] [ARGS]...")


@click.group("cli", invoke_without_command=True, cls=FreakOTPGroup, help=DESCRIPTION)
@click.version_option(__version__)
@click.option("-f", "--filename", help="Database path", default=DEFAULT_DB, type=click.Path(), envvar="FREAKOTP_DB")
@click.option("-v", "--verbose", help="Verbose output", default=False, is_flag=True)
@click.option("-c", "--counter", help="HOTP counter value", type=click.INT)
@click.option("-t", "--time", help="TOTP timestamp", type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S"]), default=None)
@click.pass_context
def cli(ctx: Context, filename: str, verbose: bool, counter: Optional[int], time: Optional[datetime]) -> None:
    ctx.obj = FreakOTP(filename=Path(filename), verbose=verbose, counter=counter, timestamp=time)
    if ctx.invoked_subcommand is None:
        freak = ctx.obj
        freak.menu()


class FreakOTP(object):

    verbose: bool
    token_db: TokenDb
    counter: Optional[int]
    timestamp: Optional[datetime]

    def __init__(
        self,
        filename: Path = DEFAULT_DB,
        verbose: bool = False,
        counter: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.verbose = verbose
        self.token_db = TokenDb(filename)
        self.counter = counter
        self.timestamp = timestamp

    def menu(self) -> None:
        "Display menu"
        try:
            token = pzp.pzp(
                self.token_db.get_tokens(),
                format_fn=lambda item: f"{item.rowid:2d}: {item}",
                fullscreen=False,
                layout="reverse-list",
                keys_binding={"qrcode": ["ctrl-q"], "uri": ["ctrl-u"]},
            )
            if token is not None:
                if self.verbose:
                    click.secho(token.details(), fg="yellow")
                print(token.calculate(timestamp=self.timestamp, counter=self.counter))
        except pzp.CustomAction as action:
            if action.action == "qrcode" and action.selected_item:
                action.selected_item.print_qrcode()
            elif action.action == "uri" and action.selected_item:
                print(action.selected_item.to_uri())

    def list(self, calculate: bool = False, long_format: bool = False) -> None:
        "List tokens"
        for token in self.token_db.get_tokens():
            if calculate:
                try:
                    otp = token.calculate(timestamp=self.timestamp, counter=self.counter)
                    if token.type == TokenType.HOTP and token.counter:
                        print(f"{otp} {token} ({token.counter=})")
                    else:
                        print(f"{otp} {token}")
                except ImportError:
                    pass
            elif long_format:
                print(f"{token.rowid:>4} {token.type.value:7} {token.algorithm:6} {token.digits:>2} {token.period:>3} {token}")
            else:
                print(token)

    def get_token(self, index: int) -> Token:
        "Get token by index"
        try:
            return self.token_db.get_tokens()[index - 1]
        except:
            raise KeyError(index)

    def find(self, arg: str) -> List[Token]:
        result: List[Token] = []
        labels: List[str] = [x.strip() for x in ([arg] if isinstance(arg, str) else arg)]
        for label in labels:
            if label.startswith("otpauth://"):
                result.append(Token(uri=label))
        for token in self.token_db.get_tokens():
            tmp = str(token).lower().strip()
            for label in labels:
                if label.lower() in tmp:
                    result.append(token)
                    break
        return result

    def import_json(self, json_filename: Path, delete_existing_data: bool = False) -> int:
        "Import FreeOTP backup into FreakOTP database"
        return self.token_db.import_json(json_filename, delete_existing_data)

    def export_json(self, json_filename: Path) -> int:
        "Export FreeOTP database using FreeOTP backup format"
        return self.token_db.export_json(json_filename)

    def add_token(
        self,
        uri: Optional[str] = None,
        rowid: Optional[int] = None,
        type: TokenType = TokenType.TOTP,
        algorithm: str = DEFAULT_ALGORITHM,
        counter: Optional[int] = None,
        digits: int = DEFAULT_DIGITS,
        issuer_int: Optional[str] = None,
        issuer_ext: Optional[str] = None,
        issuer: Optional[str] = None,
        label: Optional[str] = None,
        period: int = DEFAULT_PERIOD,
        secret: Optional[Secret] = None,
    ) -> None:
        "Add a token to the FreakOTP database"
        token = Token(
            algorithm=algorithm,
            type=type,
            counter=counter,
            digits=digits,
            issuer=issuer,
            issuer_int=issuer_int,
            issuer_ext=issuer_ext,
            label=label,
            period=period,
            secret=secret,
            token_db=self.token_db,
        )
        if self.verbose:
            click.secho(token.details(), fg="yellow")
        self.token_db.insert(token)


@cli.command(".all")
@click.pass_context
def cmd_all(ctx: Context) -> None:
    """
    Display token list

    Example: freaktop .all
    """
    freak = ctx.obj
    freak.list(calculate=True)


@cli.command(".ls")
@click.option("-l", "--long", "long_format", help="Use a long listing format", default=False, is_flag=True)
@click.pass_context
def cmd_ls(ctx: Context, long_format: bool) -> None:
    """
    Display token list

    Example: freaktop .ls
    """
    freak = ctx.obj
    freak.list(long_format=long_format)


@cli.command(".qrcode")
@click.option("-i", "--invert", help="Invert QR Code background/foreground colors", default=False, is_flag=True)
@click.argument("tokens", nargs=-1)
@click.pass_context
def cmd_qrcode(ctx: Context, invert: bool, tokens: Tuple[str]) -> None:
    """
    Display token qrcodes

    Example: freaktop .qrcode token1
    """
    freak = ctx.obj
    for token in freak.find(tokens):
        if freak.verbose:
            click.secho(token.details(), fg="yellow")
        token.print_qrcode(invert=invert)


@cli.command(".uri")
@click.argument("tokens", nargs=-1)
@click.pass_context
def cmd_uri(ctx: Context, tokens: Tuple[str]) -> None:
    """
    Display token uri

    Example: freaktop .uri token1
    """
    freak = ctx.obj
    for token in freak.find(tokens):
        if freak.verbose:
            click.secho(token.details(), fg="yellow")
        print(token.to_uri())


@cli.command(".import")
@click.option(
    "--delete-existing-data",
    help="Delete existing data from the FreakOTP datbase",
    is_flag=True,
    default=False,
)
@click.option(
    "-b", "--backup-filename", help="FreeOTP backup filename", type=click.Path(exists=True, dir_okay=False), required=True
)
@click.pass_context
def cmd_import(ctx: Context, delete_existing_data: bool, backup_filename: str) -> None:
    """
    Import tokens from freakotp-backup.json

    Example: freaktop .import --backup-filename ./freakotp-backup.json
    """
    freak = ctx.obj
    count = freak.import_json(Path(backup_filename), delete_existing_data)
    click.secho(f"{count} tokens imported")


@cli.command(".export")
@click.option(
    "-b", "--backup-filename", help="FreeOTP backup filename", type=click.Path(exists=False, dir_okay=False), required=True
)
@click.pass_context
def cmd_export(ctx: Context, backup_filename: str) -> None:
    """
    Export tokens

    Example: freaktop .expot --backup-filename ./freakotp-backup.json
    """
    freak = ctx.obj
    count = freak.export_json(Path(backup_filename))
    click.secho(f"{count} tokens exported")


@cli.command(".delete")
@click.option("-f", "--force", help="Never prompt", default=False, is_flag=True)
@click.argument("tokens", nargs=-1)
@click.pass_context
def cmd_delete(ctx: Context, force: bool, tokens: Tuple[str]) -> None:
    """
    Delete tokens

    Example: freaktop .delete token1 token2
    """
    freak = ctx.obj
    for token in freak.find(tokens):
        if freak.verbose:
            click.secho(token.details(), fg="yellow")
        if force or click.confirm(f"Do you want to remove {token} ?"):
            token.delete()


@cli.command(".add")
@click.option("--type", "type_str", help="Token type", type=click.Choice(TokenType._member_names_), default=TokenType.TOTP.value)
@click.option("-a", "--algorithm", help="Algorithm", type=click.Choice(list(ALGORITHMS)), default=DEFAULT_ALGORITHM)
@click.option("-c", "--counter", help="HOTP counter value", type=click.INT)
@click.option("-d", "--digits", help="Number of digits in one-time password", type=click.INT, default=DEFAULT_DIGITS)
@click.option("-i", "--issuer", help="Issuer")
@click.option("-l", "--label", help="Label")
@click.option("-p", "--period", help="Time-step duration in seconds", type=click.INT, default=DEFAULT_PERIOD)
@click.option("-s", "--secret", "secret_str", help="Secret key", required=True)
@click.pass_context
def cmd_add(
    ctx: Context,
    algorithm: str,
    type_str: str,
    counter: Optional[int],
    digits: int,
    issuer: Optional[str],
    label: Optional[str],
    period: int,
    secret_str: str,
) -> None:
    """
    Import a new token into the database

    Example: freaktop .add
    """
    freak = ctx.obj
    secret = Secret.from_base32(secret_str)
    type = TokenType[type_str]
    freak.add_token(
        algorithm=algorithm, type=type, counter=counter, digits=digits, issuer=issuer, label=label, period=period, secret=secret
    )


@cli.command(".default", hidden=True)
@click.argument("tokens", nargs=-1)
@click.pass_context
def cmd_default(ctx: Context, tokens: Tuple[str]) -> None:
    freak = ctx.obj
    if tokens:
        for token in freak.find(tokens):
            if freak.counter is not None and token.type == TokenType.HOTP:
                token.counter = freak.counter
            if freak.verbose:
                click.secho(token.details(), fg="yellow")
            print(token.calculate(timestamp=freak.timestamp, counter=freak.counter))
    else:
        freak.menu()


@cli.command(".help", hidden=False)
@click.argument("cmds", nargs=-1)
@click.pass_context
def cmd_help(ctx: Context, cmds: Tuple[str]) -> None:
    """Show help and exit"""
    if cmds:
        for cmd in cmds:
            command: Optional[click.Command] = ctx.parent.command.get_command(ctx=ctx.parent, cmd_name=cmd)
            if command is not None:
                click.echo(command.get_help(ctx=ctx), color=ctx.color)
    else:
        click.echo(ctx.parent.get_help(), color=ctx.color)
    ctx.exit()


def main(argv: Optional[List[str]] = None) -> int:
    if argv:
        prog_name = Path(argv[0]).name
        args = argv[1:]
    else:
        args = None
        prog_name = "freakotp"
    try:
        cli(prog_name=prog_name, args=args)
        return EXIT_SUCCESS
    except SystemExit as err:
        return err.code
    except Exception as ex:
        click.secho(f"{prog_name}: {ex}", fg="red")
        return EXIT_FAILURE
