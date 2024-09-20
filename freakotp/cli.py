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

import base64
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import appdirs
import click
import pzp
from click.core import Command, Context
from click.formatting import HelpFormatter
from click.utils import make_str
from pzp.ansi import PURPLE, RESET

from .secret import Secret
from .token import (
    ALGORITHMS,
    DEFAULT_ALGORITHM,
    DEFAULT_DIGITS,
    DEFAULT_PERIOD,
    Token,
    TokenDb,
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
CONFIG_DIR = Path(appdirs.user_config_dir(appname="FreakOTP"))
DEFAULT_DB = CONFIG_DIR / "freakotp.db"

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_PARSER_ERROR = 2


@dataclass
class KeyBinding:
    binding: str
    label: str

    @property
    def bind(self):
        return self.binding not in ("enter", "cancel")

    def __str__(self) -> str:
        if self.binding == "enter":
            return "ENTER"
        else:
            return "^" + self.binding[-1].upper()


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
@click.option("--db", help="Database path.", default=DEFAULT_DB, type=click.Path(), envvar="FREAKOTP_DB")
@click.option("-v", "--verbose", help="Verbose output.", default=False, is_flag=True)
@click.option("-c", "--counter", help="HOTP counter value.", type=click.INT)
@click.option("-t", "--time", help="TOTP timestamp.", type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S"]), default=None)
@click.option("--copy/--no-copy", help="Copy the code into the clipboard.", default=True, is_flag=True)
@click.pass_context
def cli(ctx: Context, db: str, verbose: bool, counter: Optional[int], time: Optional[datetime], copy: bool) -> None:
    ctx.obj = FreakOTP(db_filename=Path(db), verbose=verbose, counter=counter, timestamp=time, copy=copy)
    if ctx.invoked_subcommand is None:
        freak = ctx.obj
        freak.menu()


class FreakOTP(object):
    verbose: bool
    token_db: TokenDb
    counter: Optional[int]
    timestamp: Optional[datetime]
    copy: bool
    key_bindings = {
        "enter": KeyBinding(binding="enter", label="Show OTP"),
        "cancel": KeyBinding(binding="ctrl-c", label="Exit"),
        "qrcode": KeyBinding(binding="ctrl-q", label="QR-Code"),
        "uri": KeyBinding(binding="ctrl-u", label="URI"),
        "insert-token": KeyBinding(binding="ctrl-i", label="Insert"),
        "edit-token": KeyBinding(binding="ctrl-o", label="Edit"),
        "delete-token": KeyBinding(binding="ctrl-x", label="Delete"),
    }

    def __init__(
        self,
        db_filename: Path = DEFAULT_DB,
        verbose: bool = False,
        counter: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        copy: bool = True,
    ):
        self.verbose = verbose
        self.token_db = TokenDb(db_filename)
        self.counter = counter
        self.timestamp = timestamp
        self.copy = copy

    def menu(self) -> None:
        "Display menu"
        try:
            token = pzp.pzp(
                self.token_db.get_tokens,
                format_fn=lambda item: f"{item.rowid:2d}: {item}",
                fullscreen=False,
                layout="reverse-list",
                header_str="  ".join([f"{PURPLE}{x}{RESET} {x.label}" for x in self.key_bindings.values()]),
                keys_binding=(dict([(k, [v.binding]) for k, v in self.key_bindings.items() if v.bind])),
                auto_refresh=1,
            )
            if token is not None:
                if self.verbose:
                    click.secho(token.details(), fg="yellow")
                otp = token.calculate(timestamp=self.timestamp, counter=self.counter)
                self.copy_into_clipboard(otp)
                print(otp)
        except pzp.CustomAction as action:
            if action.action == "qrcode" and action.selected_item:
                action.selected_item.print_qrcode()
            elif action.action == "uri" and action.selected_item:
                print(action.selected_item.to_uri())
            elif action.action == "delete-token" and action.selected_item:
                self.delete_tokens([action.selected_item])
            elif action.action == "insert-token" and action.selected_item:
                self.add_token()
            elif action.action == "edit-token" and action.selected_item:
                self.edit_token(action.selected_item)

    def list(
        self,
        calculate: bool = False,
        long_format: bool = False,
        tokens: Union[None, str, Token, Sequence[str], Sequence[Token]] = None,
    ) -> None:
        "List tokens"
        if tokens:
            tokens_list: List[Token] = self.find(tokens)
        else:
            tokens_list = self.token_db.get_tokens()
        for i, token in enumerate(tokens_list):
            if calculate:
                try:
                    otp = token.calculate(timestamp=self.timestamp, counter=self.counter)
                    if i == 0:
                        self.copy_into_clipboard(otp)
                    if token.type == TokenType.HOTP and token.counter:
                        counter = f"({token.counter})"
                    else:
                        counter = ""
                    if long_format:
                        print(
                            f"{otp:8} {token.rowid:>4} {token.type.value:7} {token.algorithm:6} {token.digits:>2} {token.period:>3} {token} {counter}"
                        )
                    else:
                        print(f"{otp} {token} {counter}")
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
        except Exception:
            raise KeyError(index)

    def find(self, arg: Union[str, Token, Sequence[str], Sequence[Token]]) -> List[Token]:
        args_list: Sequence[Union[str, Token]] = arg if isinstance(arg, (tuple, list)) else [arg]
        result: List[Token] = [x for x in args_list if isinstance(x, Token)]
        labels: List[str] = [x for x in args_list if isinstance(x, str)]
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
        "Import backup into FreakOTP database"
        return self.token_db.import_json(json_filename, delete_existing_data)

    def export_json(self, json_filename: Path) -> int:
        "Export FreeOTP database using FreeOTP backup format"
        return self.token_db.export_json(json_filename)

    def add_token(
        self,
        uri: Optional[str] = None,
        rowid: Optional[int] = None,
        type_str: Optional[str] = "TOTP",
        algorithm: str = DEFAULT_ALGORITHM,
        counter: Optional[int] = None,
        digits: int = DEFAULT_DIGITS,
        issuer_int: Optional[str] = None,
        issuer_ext: Optional[str] = None,
        issuer: Optional[str] = None,
        label: Optional[str] = None,
        period: int = DEFAULT_PERIOD,
        secret_str: Optional[str] = None,
    ) -> Token:
        "Add a token to the FreakOTP database"
        self.title("Add token")
        if not secret_str and not uri:
            uri_or_secret = pzp.prompt("Secret key Base32 or URI (otpauth://)", show_default=False).strip()
            if uri_or_secret.startswith("otpauth"):
                uri = uri_or_secret
                secret: Secret = None
            else:
                secret = Secret.from_base32(uri_or_secret)
                issuer = pzp.prompt("Issuer", default=issuer)
                label = pzp.prompt("Label", default=label)
                type_str = pzp.pzp(
                    header_str="Token type:",
                    layout="reverse-list",
                    candidates=TokenType._member_names_,
                    fullscreen=False,
                )
                print(f"Token type: {type_str}")
                algorithm = pzp.pzp(
                    header_str="Algorithm:",
                    layout="reverse-list",
                    candidates=list(ALGORITHMS),
                    fullscreen=False,
                )
                print(f"Algorithm: {algorithm}")
                if type_str == "HOTP":
                    counter = pzp.prompt("HOTP counter value", type=click.INT, default=counter)
                digits = pzp.prompt("Number of digits in one-time password", type=click.INT, default=digits)
                if type_str != "HOTP":
                    period = pzp.prompt("Time-step duration in seconds", type=click.INT, default=period)
        token = Token(
            uri=uri,
            type=TokenType[type_str] if type_str else None,
            algorithm=algorithm,
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
        click.secho("Token added", fg="green")
        return token

    def edit_token(self, token: Token) -> Token:
        "Edit a token"
        self.title(f"Edit token {token}")
        token.secret = Secret.from_base32(pzp.prompt("Secret", default=token.secret.to_base32()))
        token.issuer = pzp.prompt("Issuer", default=token.issuer)
        token.label = pzp.prompt("Label", default=token.label)
        type_str = pzp.pzp(
            header_str="Token type:",
            layout="reverse-list",
            candidates=TokenType._member_names_,
            input=token.type.value,
            fullscreen=False,
        )
        token.type = TokenType[type_str] if type_str else None
        print(f"Token type: {type_str}")
        token.algorithm = pzp.pzp(
            header_str="Algorithm:",
            layout="reverse-list",
            candidates=list(ALGORITHMS),
            input=token.algorithm,
            fullscreen=False,
        )
        print(f"Algorithm: {token.algorithm}")
        if type_str == "HOTP":
            token.counter = pzp.prompt("HOTP counter value", type=click.INT, default=token.counter)
        token.digits = pzp.prompt("Number of digits in one-time password", type=click.INT, default=token.digits)
        if type_str != "HOTP":
            token.period = pzp.prompt("Time-step duration in seconds", type=click.INT, default=token.period)
        if self.verbose:
            click.secho(token.details(), fg="yellow")
        self.token_db.update(token)
        click.secho("Token updated", fg="green")
        return token

    def delete_tokens(self, tokens: Tuple[str], force: bool = False) -> None:
        "Delete tokens"
        count = 0
        self.title("Delete token")
        for token in self.find(tokens):
            if self.verbose:
                click.secho(token.details(), fg="yellow")
            if force or click.confirm(f"Do you want to remove {token} ?"):
                token.delete()
                count = count + 1
        if count == 1:
            click.secho("Token deleted", fg="green")
        else:
            click.secho(f"{count} tokens deleted", fg="green")

    def title(self, title: str) -> None:
        click.secho(f"{title:66}", bg="blue", fg="white", bold=True)

    def copy_into_clipboard(self, otp: str) -> None:
        "Copy data into the clipboard"
        if self.copy:
            data = base64.b64encode(otp.encode("utf-8")).decode("ascii")
            data = f"\033]52;c;{data}\a"
            if "TMUX" in os.environ:
                data = f"\033Ptmux;\033{data}\033\\"
            sys.stdout.write(data)
            sys.stdout.flush()


@cli.command(".otp")
@click.argument("tokens", nargs=-1)
@click.option("-l", "--long", "long_format", help="Use a long listing format", default=False, is_flag=True)
@click.pass_context
def cmd_otp(ctx: Context, long_format: bool, tokens: Tuple[str]) -> None:
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
def cmd_ls(ctx: Context, long_format: bool, tokens: Tuple[str]) -> None:
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
def cmd_delete(ctx: Context, force: bool, tokens: Tuple[str]) -> None:
    """
    Delete tokens

    Example: freaktop .delete token1 token2
    """
    freak = ctx.obj
    freak.delete_tokens(tokens, force)


@cli.command(".edit")
@click.argument("tokens", nargs=-1)
@click.pass_context
def cmd_edit(ctx: Context, tokens: Tuple[str]) -> None:
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
    counter: Optional[int],
    digits: int,
    issuer: Optional[str],
    label: Optional[str],
    period: int,
    secret_str: Optional[str],
    uri: Optional[str],
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
def cmd_default(ctx: Context, tokens: Tuple[str]) -> None:
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
