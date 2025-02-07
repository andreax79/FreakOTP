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

import typing as t
from datetime import datetime
from pathlib import Path

import click
import platformdirs
from click.core import Command, Context
from click.formatting import HelpFormatter
from click.utils import make_str

from .freakotp import FreakOTP
from .token import (
    ALGORITHMS,
    DEFAULT_ALGORITHM,
    DEFAULT_DIGITS,
    DEFAULT_PERIOD,
    Token,
    TokenType,
)

__author__ = "Andrea Bonomi <andrea.bonomi@gmail.com>"
__version__ = "3.0.7"
__all__ = [
    "main",
    "FreakOTP",
    "Token",
    "DEFAULT_PERIOD",
    "DEFAULT_ALGORITHM",
    "DEFAULT_DIGITS",
]

DESCRIPTION = "FreakOTP is a command line two-factor authentication application."
CONFIG_DIR = Path(platformdirs.user_config_dir(appname="FreakOTP"))
DEFAULT_DB = CONFIG_DIR / "freakotp.db"

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_PARSER_ERROR = 2


class FreakOTPGroup(click.Group):
    def resolve_command(self, ctx: Context, args: t.List[str]) -> t.Tuple[t.Optional[str], t.Optional[Command], t.List[str]]:
        is_cmd = args and make_str(args[0]).startswith(".")
        if is_cmd:
            return super().resolve_command(ctx, args)
        else:
            return ".default", self.get_command(ctx, ".default"), args

    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        formatter.write_usage(ctx.command_path, "[OPTIONS] [COMMAND|[TOKENS]...] [ARGS]...")


@click.group("cli", invoke_without_command=True, cls=FreakOTPGroup, help=DESCRIPTION)
@click.version_option(__version__)
@click.option("--db", help="Database path.", default=DEFAULT_DB, type=click.Path(), envvar="FREAKOTP_DB")
@click.option("-v", "--verbose", help="Verbose output.", default=False, is_flag=True)
@click.option("-c", "--counter", help="HOTP counter value.", type=click.INT)
@click.option("-t", "--time", help="TOTP timestamp.", type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S"]), default=None)
@click.option("--copy/--no-copy", help="Copy the code into the clipboard.", default=True, is_flag=True)
@click.option("--all/--no-all", help="Show all codes.", default=False, is_flag=True)
@click.pass_context
def cli(
    ctx: Context,
    db: str,
    verbose: bool,
    counter: t.Optional[int],
    time: t.Optional[datetime],
    copy: bool,
    all: bool,
) -> None:
    ctx.obj = FreakOTP(
        db_filename=Path(db),
        verbose=verbose,
        counter=counter,
        timestamp=time,
        copy_to_clipboard=copy,
        show_codes=all,
    )
    if ctx.invoked_subcommand is None:
        freak = ctx.obj
        freak.menu()


@cli.command(".otp")
@click.argument("tokens", nargs=-1)
@click.option("-l", "--long", "long_format", help="Use a long listing format", default=False, is_flag=True)
@click.pass_context
def cmd_otp(ctx: Context, long_format: bool, tokens: t.Tuple[str]) -> None:
    """
    Display OTPs

    Example: freaktop .otp
    """
    freak = ctx.obj
    freak.list(calculate=True, long_format=long_format, tokens=tokens)


@cli.command(".ls")
@click.argument("tokens", nargs=-1)
@click.option("-l", "--long", "long_format", help="Use a long listing format", default=False, is_flag=True)
@click.pass_context
def cmd_ls(ctx: Context, long_format: bool, tokens: t.Tuple[str]) -> None:
    """
    Display token list

    Example: freaktop .ls
    """
    freak = ctx.obj
    freak.list(long_format=long_format, tokens=tokens)


@cli.command(".qrcode")
@click.option("-i", "--invert", help="Invert QR Code background/foreground colors", default=False, is_flag=True)
@click.argument("tokens", nargs=-1)
@click.pass_context
def cmd_qrcode(ctx: Context, invert: bool, tokens: t.Tuple[str]) -> None:
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
def cmd_uri(ctx: Context, tokens: t.Tuple[str]) -> None:
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
    help="Delete existing data from the FreakOTP database",
    is_flag=True,
    default=False,
)
@click.option("-f", "--filename", help="FreeOTP backup filename", type=click.Path(exists=True, dir_okay=False), required=True)
@click.pass_context
def cmd_import(ctx: Context, delete_existing_data: bool, filename: str) -> None:
    """
    Import tokens from backup

    Example: freaktop .import --filename ./freakotp-backup.json
    """
    freak = ctx.obj
    count = freak.import_json(Path(filename), delete_existing_data)
    click.secho(f"{count} tokens imported", fg="green")


@cli.command(".export")
@click.option("-f", "--filename", help="FreeOTP backup filename", type=click.Path(exists=False, dir_okay=False), required=True)
@click.pass_context
def cmd_export(ctx: Context, filename: str) -> None:
    """
    Export tokens

    Example: freaktop .export --filename ./freakotp-backup.json
    """
    freak = ctx.obj
    count = freak.export_json(Path(filename))
    click.secho(f"{count} tokens exported", fg="green")


@cli.command(".delete")
@click.option("-f", "--force", help="Never prompt", default=False, is_flag=True)
@click.argument("tokens", nargs=-1)
@click.pass_context
def cmd_delete(ctx: Context, force: bool, tokens: t.Tuple[str]) -> None:
    """
    Delete tokens

    Example: freaktop .delete token1 token2
    """
    freak = ctx.obj
    freak.delete_tokens(tokens, force)


@cli.command(".edit")
@click.argument("tokens", nargs=-1)
@click.pass_context
def cmd_edit(ctx: Context, tokens: t.Tuple[str]) -> None:
    """
    Edit tokens

    Example: freaktop .edit token1
    """
    freak = ctx.obj
    for token in freak.find(tokens):
        freak.edit_token(token)


@cli.command(".add")
@click.option("--type", "type_str", help="Token type", type=click.Choice(TokenType._member_names_), default=TokenType.TOTP.value)
@click.option("-a", "--algorithm", help="Algorithm", type=click.Choice(list(ALGORITHMS)), default=DEFAULT_ALGORITHM)
@click.option("-c", "--counter", help="HOTP counter value", type=click.INT)
@click.option("-d", "--digits", help="Number of digits in one-time password", type=click.INT, default=DEFAULT_DIGITS)
@click.option("-i", "--issuer", help="Issuer")
@click.option("-l", "--label", help="Label")
@click.option("-p", "--period", help="Time-step duration in seconds", type=click.INT, default=DEFAULT_PERIOD)
@click.option("-s", "--secret", "secret_str", help="Secret key Base32")
@click.option("-u", "--uri", help="URI (otpauth://)")
@click.pass_context
def cmd_add(
    ctx: Context,
    algorithm: str,
    type_str: str,
    counter: t.Optional[int],
    digits: int,
    issuer: t.Optional[str],
    label: t.Optional[str],
    period: int,
    secret_str: t.Optional[str],
    uri: t.Optional[str],
) -> None:
    """
    Import a new token into the database

    Example: freaktop .add
    """
    freak = ctx.obj
    freak.add_token(
        uri=uri,
        algorithm=algorithm,
        type_str=type_str,
        counter=counter,
        digits=digits,
        issuer=issuer,
        label=label,
        period=period,
        secret_str=secret_str,
    )


@cli.command(".default", hidden=True)
@click.argument("tokens", nargs=-1)
@click.pass_context
def cmd_default(ctx: Context, tokens: t.Tuple[str]) -> None:
    freak = ctx.obj
    if tokens:
        for i, token in enumerate(freak.find(tokens)):
            if freak.counter is not None and token.type == TokenType.HOTP:
                token.counter = freak.counter
            if freak.verbose:
                click.secho(token.details(), fg="yellow")
            otp = token.calculate(timestamp=freak.timestamp, counter=freak.counter)
            if i == 0:  # copy the first code into the clipboard
                freak.copy_into_clipboard(otp)
            print(otp)
    else:
        freak.menu()


@cli.command(".help", hidden=False)
@click.argument("cmds", nargs=-1)
@click.pass_context
def cmd_help(ctx: Context, cmds: t.Tuple[str]) -> None:
    """Show help and exit"""
    if cmds:
        for cmd in cmds:
            command: t.Optional[click.Command] = ctx.parent.command.get_command(ctx=ctx.parent, cmd_name=cmd)
            if command is not None:
                click.echo(command.get_help(ctx=ctx), color=ctx.color)
    else:
        click.echo(ctx.parent.get_help(), color=ctx.color)
    ctx.exit()


def main(argv: t.Optional[t.List[str]] = None) -> int:
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
