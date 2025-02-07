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
import typing as t
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click
import pzp
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

__all__ = [
    "FreakOTP",
]

SPINNER_STYLES = [
    "",
    "◯◔◒◕●",
    " ▁▂▃▄▅▆▇█",
    " ▏▎▍▌▋▊▉",
]


@dataclass
class KeyBinding:
    binding: str
    label: str

    @property
    def bind(self) -> bool:
        return self.binding not in ("enter", "cancel")

    def __str__(self) -> str:
        if self.binding == "enter":
            return "ENTER"
        else:
            return "^" + self.binding[-1].upper()


class FreakOTP:
    verbose: bool  # Verbose output
    token_db: TokenDb  # Token database
    counter: t.Optional[int]  # HOTP counter value
    timestamp: t.Optional[datetime]  # TOTP timestamp
    copy_to_clipboard: bool  # Copy the code into the clipboard flag
    show_codes: bool  # Show all OTP flag
    key_bindings = {
        "enter": KeyBinding(binding="enter", label="Show OTP"),
        "cancel": KeyBinding(binding="ctrl-c", label="Exit"),
        "all": KeyBinding(binding="ctrl-s", label="Show All"),
        "qrcode": KeyBinding(binding="ctrl-q", label="QR-Code"),
        "uri": KeyBinding(binding="ctrl-u", label="URI"),
        "insert-token": KeyBinding(binding="ctrl-i", label="Insert"),
        "edit-token": KeyBinding(binding="ctrl-o", label="Edit"),
        "delete-token": KeyBinding(binding="ctrl-x", label="Delete"),
    }

    def __init__(
        self,
        db_filename: Path,
        verbose: bool = False,
        counter: t.Optional[int] = None,
        timestamp: t.Optional[datetime] = None,
        copy_to_clipboard: bool = True,
        show_codes: bool = False,
    ):
        self.verbose = verbose
        self.token_db = TokenDb(db_filename)
        self.counter = counter
        self.timestamp = timestamp
        self.copy_to_clipboard = copy_to_clipboard
        self.show_codes = show_codes

    def menu(self) -> None:
        "Display menu"
        while True:
            try:
                if self.show_codes:
                    # format_fn = lambda item: f"{item.rowid:2d}: {item.calculate():>8} {item.spinner(SPINNER_STYLE_1)} [{item.time_left():>2}] {item}"
                    format_fn = lambda item: f"{item.rowid:2d}: {item.calculate():>8} [{item.time_left():>2}] {item}"
                else:
                    format_fn = lambda item: f"{item.rowid:2d}: {item}"
                token = pzp.pzp(
                    self.token_db.get_tokens,
                    format_fn=format_fn,
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
                break
            except pzp.CustomAction as action:
                if action.action == "qrcode" and action.selected_item:
                    action.selected_item.print_qrcode()
                elif action.action == "uri" and action.selected_item:
                    print(action.selected_item.to_uri())
                elif action.action == "delete-token" and action.selected_item:
                    self.delete_tokens(tuple([action.selected_item]))
                elif action.action == "insert-token" and action.selected_item:
                    self.add_token()
                elif action.action == "edit-token" and action.selected_item:
                    self.edit_token(action.selected_item)
                elif action.action == "all":
                    self.show_codes = not self.show_codes
                    continue
                break

    def list(
        self,
        calculate: bool = False,
        long_format: bool = False,
        tokens: t.Union[None, str, Token, t.Sequence[str], t.Sequence[Token]] = None,
    ) -> None:
        "List tokens"
        if tokens:
            tokens_list: t.List[Token] = self.find(tokens)
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

    def find(self, arg: t.Union[str, Token, t.Sequence[str], t.Sequence[Token]]) -> t.List[Token]:
        args_list: t.Sequence[t.Union[str, Token]] = arg if isinstance(arg, (tuple, list)) else [arg]
        result: t.List[Token] = [x for x in args_list if isinstance(x, Token)]
        labels: t.List[str] = [x for x in args_list if isinstance(x, str)]
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
        uri: t.Optional[str] = None,
        rowid: t.Optional[int] = None,
        type_str: t.Optional[str] = "TOTP",
        algorithm: str = DEFAULT_ALGORITHM,
        counter: t.Optional[int] = None,
        digits: int = DEFAULT_DIGITS,
        issuer_int: t.Optional[str] = None,
        issuer_ext: t.Optional[str] = None,
        issuer: t.Optional[str] = None,
        label: t.Optional[str] = None,
        period: int = DEFAULT_PERIOD,
        secret_str: t.Optional[str] = None,
    ) -> Token:
        "Add a token to the FreakOTP database"
        self.title("Add token")
        if not secret_str and not uri:
            uri_or_secret = pzp.prompt("Secret key Base32 or URI (otpauth://)", show_default=False).strip()
            if uri_or_secret.startswith("otpauth"):
                uri = uri_or_secret
                secret: t.Optional[Secret] = None
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
            type=TokenType[type_str] if type_str else TokenType.TOTP,
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
        token.type = TokenType[type_str] if type_str else TokenType.TOTP
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

    def delete_tokens(self, tokens: t.Tuple[str], force: bool = False) -> None:
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
        if self.copy_to_clipboard:
            data = base64.b64encode(otp.encode("utf-8")).decode("ascii")
            data = f"\033]52;c;{data}\a"
            if "TMUX" in os.environ:
                data = f"\033Ptmux;\033{data}\033\\"
            sys.stdout.write(data)
            sys.stdout.flush()
