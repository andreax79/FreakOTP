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

import hashlib
import hmac
import json
import math
import sqlite3
import struct
import time
import typing as t
import urllib.parse
from contextlib import closing
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import cast

import click
import qrcode  # type: ignore

from .secret import Secret
from .sql import (
    SQL_CREATE_TOKENS_TABLE,
    SQL_DELETE_TOKEN,
    SQL_DROP_TOKENS_TABLE,
    SQL_INSERT_TOKEN,
    SQL_SELECT_TOKENS,
    SQL_UPDATE_TOKEN,
    TOKEN_COLUMNS,
)

__all__ = [
    "Token",
    "TokenDb",
    "TokenType",
    "ALGORITHMS",
    "DEFAULT_PERIOD",
    "DEFAULT_ALGORITHM",
    "DEFAULT_DIGITS",
]

ALGORITHMS = {
    "SHA1": hashlib.sha1,
    "SHA256": hashlib.sha256,
    "SHA512": hashlib.sha512,
    "MD5": hashlib.md5,
}

DEFAULT_PERIOD = 30
DEFAULT_ALGORITHM = "SHA1"
DEFAULT_DIGITS = 6

JsonData = t.Dict[str, t.Union[str, int, t.List[int], None]]


class TokenType(Enum):
    TOTP = "TOTP"
    HOTP = "HOTP"
    SECURID = "SecurID"


class EncodeType(Enum):
    BASE32 = "BASE32"
    HEX = "HEX"
    INT_LIST = "INT_LIST"


class Token:
    data: t.Union[str, JsonData, None] = None
    token_db: t.Optional["TokenDb"] = None
    rowid: t.Optional[int] = None
    type: TokenType = TokenType.TOTP
    algorithm: str = DEFAULT_ALGORITHM
    counter: t.Optional[int] = None
    digits: int = DEFAULT_DIGITS
    issuer_int: t.Optional[str] = None
    issuer_ext: t.Optional[str] = None
    issuer: t.Optional[str] = None
    label: t.Optional[str] = None
    period: int = DEFAULT_PERIOD
    exp_date: t.Optional[str] = None
    pin: t.Optional[str] = None
    serial: t.Optional[str] = None
    secret: Secret = Secret()

    def __init__(
        self,
        data: t.Optional[JsonData] = None,
        uri: t.Optional[str] = None,
        rowid: t.Optional[int] = None,
        type: TokenType = TokenType.TOTP,
        algorithm: str = DEFAULT_ALGORITHM,
        counter: t.Optional[int] = None,
        digits: int = DEFAULT_DIGITS,
        issuer_int: t.Optional[str] = None,
        issuer_ext: t.Optional[str] = None,
        issuer: t.Optional[str] = None,
        label: t.Optional[str] = None,
        period: int = DEFAULT_PERIOD,
        exp_data: t.Optional[str] = None,
        pin: t.Optional[str] = None,
        serial: t.Optional[str] = None,
        secret: t.Optional[Secret] = None,
        token_db: t.Optional["TokenDb"] = None,
    ) -> None:
        self.token_db = token_db
        self.rowid = rowid
        self.type = type
        self.algorithm = algorithm
        if self.type == TokenType.HOTP:
            self.counter = counter or 0
        else:
            self.counter = counter
        self.digits = digits
        self.issuer_int = issuer_int
        self.issuer_ext = issuer_ext
        self.issuer = issuer
        if self.issuer and not self.issuer_int:
            self.issuer_int = self.issuer
        if self.issuer and not self.issuer_ext:
            self.issuer_ext = self.issuer
        self.label = label
        self.period = period
        self.exp_date = exp_data
        self.pin = pin
        self.serial = serial
        self.secret = secret or Secret()
        # Parse data or uri
        if data:
            self._parse_data(data)
        elif uri:
            self._parse_uri(uri)

    def _parse_data(self, data: JsonData) -> None:
        self.data = data
        self.rowid = cast(t.Optional[int], data.get("rowid"))
        self.type = TokenType[cast(str, data.get("type")).upper()]
        self.algorithm = cast(str, data.get("algo")) or DEFAULT_ALGORITHM
        self.counter = cast(int, data.get("counter"))
        self.digits = cast(int, data.get("digits")) or DEFAULT_DIGITS
        self.issuer_int = cast(str, data.get("issuer_int") or data.get("issuerInt"))
        self.issuer_ext = cast(str, data.get("issuer_ext") or data.get("issuerExt"))
        self.issuer = self.issuer_int or self.issuer_ext
        self.label = cast(str, data.get("label"))
        self.period = cast(int, data.get("period")) or DEFAULT_PERIOD
        self.exp_data = cast(str, data.get("exp_date"))
        self.pin = cast(str, data.get("pin"))
        self.serial = cast(str, data.get("serial"))
        self.secret = Secret.from_base32(cast(str, data["secret"]))

    def _parse_uri(self, uri: str) -> None:
        uri_components = urllib.parse.urlparse(uri)
        query = dict(urllib.parse.parse_qsl(uri_components.query))
        self.rowid = None
        try:
            self.type = TokenType[uri_components.netloc.upper()]
        except Exception:
            raise Exception("Error parsing URI, invalid token type")
        self.algorithm = query.get("algorithm") or DEFAULT_ALGORITHM
        self.counter = int(cast(str, query.get("counter"))) if "counter" in query else 0
        self.digits = int(cast(str, query.get("digits"))) if "digest" in query else DEFAULT_DIGITS
        if ":" in uri_components.path:
            self.issuer, self.label = uri_components.path.strip("/").split(":", 1)
            self.issuer_int = self.issuer
            self.issuer_ext = self.issuer
        else:
            self.label = uri_components.path.strip("/")
            self.issuer = None
            self.issuer_int = None
            self.issuer_ext = None
        self.period = int(cast(str, query.get("period"))) if "period" in query else DEFAULT_PERIOD
        self.exp_date = None
        self.pin = None
        self.serial = None
        self.secret = Secret.from_base32(cast(str, query.get("secret")))

    def calculate(self, timestamp: t.Optional[t.Union[int, datetime]] = None, counter: t.Optional[int] = None) -> str:
        """
        Calculate the code for the token

        :param timestamp: timestamp to calculate the code for
        :param counter: counter to calculate the code for (for HOTP)
        :returns: the code
        """
        if self.type == TokenType.SECURID:
            try:
                return self._calculate_securid()
            except Exception:
                return "??????"
        algorithm = ALGORITHMS.get(self.algorithm, hashlib.sha1)
        if self.type == TokenType.HOTP:
            value = counter if counter is not None else self.counter
        elif timestamp is not None and isinstance(timestamp, datetime):
            value = int(timestamp.timestamp()) // self.period
        elif timestamp is not None:
            value = timestamp // self.period
        else:
            value = int(int(time.time()) / self.period)
        t = struct.pack(">q", value)
        hmac_ = hmac.HMAC(self.secret.to_bytes(), t, algorithm).digest()
        offset = hmac_[-1] & 0x0F
        code = struct.unpack(">L", hmac_[offset : offset + 4])[0]
        frmt = "{0:0%dd}" % self.digits
        return frmt.format((code & 0x7FFFFFFF) % int(math.pow(10, self.digits)))

    def time_left(self, for_time: t.Union[int, datetime, None] = None) -> t.Optional[int]:
        """
        Time until next token

        :param for_time: time to calculate the time left for
        :returns: seconds
        """
        if self.type == TokenType.SECURID:
            try:
                from securid.jsontoken import JSONTokenFile

                token = JSONTokenFile(data=self.to_dict()).get_token()
                return token.time_left(for_time)
            except Exception:
                return None

        elif self.type == TokenType.TOTP:
            if for_time is None:
                for_time = datetime.utcnow()
            elif not isinstance(for_time, datetime):
                for_time = datetime.utcfromtimestamp(int(for_time))
            result = (self.period - for_time.second) % self.period
            if result == 0:
                result = self.period
            return result

        else:
            return None

    def spinner(self, spinner_chars: str) -> str:
        """
        Return a spinner character based on the time left to the next token

        :param spinner_chars: string of spinner characters
        :returns: spinner
        """
        if not spinner_chars:
            return ""
        time_left = self.time_left()
        if time_left is None:
            return ""
        t = min(time_left * len(spinner_chars) // self.period, len(spinner_chars) - 1)
        return spinner_chars[t]

    def _calculate_securid(self) -> str:
        from securid.jsontoken import JSONTokenFile

        return JSONTokenFile(data=self.to_dict()).get_token().now()

    def to_dict(self, encode_type: EncodeType = EncodeType.INT_LIST) -> JsonData:
        """
        Return token as dict

        :param encode_type: encoding type for the secret
        :returns: token as dict
        """
        if encode_type == EncodeType.INT_LIST:
            secret: t.Union[t.List[int], str] = self.secret.to_int_list()
        elif encode_type == EncodeType.HEX:
            secret = self.secret.to_hex()
        else:
            secret = self.secret.to_base32()
        data: JsonData = {
            "type": self.type.value,
            "algorithm": self.algorithm,
            "counter": self.counter,
            "digits": self.digits,
            "issuer": self.issuer,
            "label": self.label,
            "period": self.period,
            "secret": secret,
        }
        for key in ("exp_date", "pin", "serial"):
            if getattr(self, key) is not None:
                data[key] = getattr(self, key)
        return data

    def to_json(self) -> str:
        "Return token as json"
        return json.dumps(self.to_dict(), indent=2)

    def to_uri(self) -> str:
        "Return token as otpauth uri"
        data: t.Dict[str, t.Union[str, int]] = {}
        if self.algorithm:
            data["algorithm"] = self.algorithm
        if self.digits:
            data["digits"] = self.digits
        if self.period and self.type != TokenType.HOTP:
            data["period"] = self.period
        if self.type == TokenType.HOTP:
            data["counter"] = self.counter or 0
        data["secret"] = self.secret.to_base32()
        label = ":".join([x.strip() for x in [self.issuer, self.label] if x])
        query = urllib.parse.urlencode(data)
        return urllib.parse.urlunparse(("otpauth", self.type.value.lower(), label, None, query, None))

    def details(self) -> str:
        "Return token details as string"
        result: t.List[str] = []
        for key, value in self.to_dict(encode_type=EncodeType.BASE32).items():
            result.append(f"{key.title() + ':':<10} {value}")
        return "\n".join(result)

    def print_qrcode(self, invert: bool = True) -> None:
        "Print token as qrcode"
        click.secho(f"{self}", fg="green")
        qr = qrcode.QRCode()
        qr.add_data(self.to_uri())
        qr.print_ascii(invert=invert)

    def delete(self) -> None:
        "Delete this token"
        if self.rowid is not None and self.token_db is not None:
            self.token_db.delete(self.rowid)

    def __str__(self) -> str:
        if self.issuer or self.label:
            return ":".join([x.strip() for x in [self.issuer, self.label] if x])
        elif self.rowid is not None:
            return f"#{self.rowid}"  # type: ignore
        else:
            return "?"


class TokenDb:
    def __init__(self, filename: Path) -> None:
        self.filename = filename
        self.filename.parent.mkdir(parents=True, exist_ok=True)

    def open_db(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(self.filename)
        except TypeError:  # Python < 3.7
            connection = sqlite3.connect(str(self.filename))
        with closing(connection.cursor()) as cursor:
            cursor.execute(SQL_CREATE_TOKENS_TABLE)
        return connection

    def get_tokens(self) -> t.List[Token]:
        result: t.List[Token] = []
        with closing(self.open_db()) as connection:
            with closing(connection.cursor()) as cursor:
                rows = cursor.execute(SQL_SELECT_TOKENS).fetchall()
                for values in rows:
                    data = dict(zip(TOKEN_COLUMNS, values))
                    result.append(Token(data, token_db=self))
        return result

    def delete(self, rowid: int) -> None:
        "Delete a token by rowid"
        with closing(self.open_db()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(SQL_DELETE_TOKEN, [rowid])
                connection.commit()

    def insert(self, token: Token) -> None:
        "Insert a token into the database"
        with closing(self.open_db()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    SQL_INSERT_TOKEN,
                    (
                        token.type.value,
                        token.algorithm,
                        token.counter,
                        token.digits,
                        token.issuer_int,
                        token.issuer_ext,
                        token.label,
                        token.period,
                        token.exp_date,
                        token.pin,
                        token.serial,
                        token.secret.to_base32(),
                    ),
                )
                connection.commit()

    def update(self, token: Token) -> None:
        "Update a token in the database"
        with closing(self.open_db()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    SQL_UPDATE_TOKEN,
                    (
                        token.type.value,
                        token.algorithm,
                        token.counter,
                        token.digits,
                        token.issuer_int,
                        token.issuer_ext,
                        token.label,
                        token.period,
                        token.exp_date,
                        token.pin,
                        token.serial,
                        token.secret.to_base32(),
                        token.rowid,
                    ),
                )
                connection.commit()

    def truncate(self) -> None:
        "Delete all the tokens"
        with closing(self.open_db()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(SQL_DROP_TOKENS_TABLE)
                cursor.execute(SQL_CREATE_TOKENS_TABLE)
                connection.commit()

    def import_json(self, json_filename: Path, delete_existing_data: bool = False) -> int:
        "Import FreeOTP backup into FreakOTP database"
        with json_filename.open("r") as f:
            self.data = json.loads(f.read())
        count = 0
        with closing(self.open_db()) as connection:
            with closing(connection.cursor()) as cursor:
                if delete_existing_data:
                    cursor.execute(SQL_DROP_TOKENS_TABLE)
                cursor.execute(SQL_CREATE_TOKENS_TABLE)
                for token in self.data["tokens"]:
                    secret = Secret.from_int_list(token["secret"])
                    cursor.execute(
                        SQL_INSERT_TOKEN,
                        (
                            token.get("type"),
                            token.get("algo") or DEFAULT_ALGORITHM,
                            token.get("counter"),
                            token.get("digits") or DEFAULT_DIGITS,
                            token.get("issuerInt"),
                            token.get("issuerExt"),
                            token.get("label"),
                            token.get("period") or DEFAULT_PERIOD,
                            token.get("exp_date"),
                            token.get("pin"),
                            token.get("serial"),
                            secret.to_base32(),
                        ),
                    )
                    count = count + 1
                connection.commit()
        return count

    def export_json(self, json_filename: Path) -> int:
        "Export FreeOTP database using FreeOTP backup format"
        tokens: t.List[JsonData] = []
        for token_obj in self.get_tokens():
            token = token_obj.to_dict()
            token["issuerInt"] = token["issuer"]
            token["issuerExt"] = token["issuer"]
            del token["issuer"]
            tokens.append(token)
        token_order: t.List[str] = [f"{token['issuerInt']}:{token['label']}" for token in tokens]
        result = {"tokenOrder": token_order, "tokens": tokens}
        with json_filename.open("w") as f:
            json.dump(result, f, indent=2)
        return len(tokens)
