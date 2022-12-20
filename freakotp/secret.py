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
from typing import Any, List

__all__ = ["Secret"]


class Secret:
    def __init__(self, secret: bytes = b""):
        self.secret = secret

    @classmethod
    def from_int_list(cls, secret: List[int]) -> "Secret":
        return Secret(bytes([(x + 256) % 256 for x in secret]))

    @classmethod
    def from_base32(cls, secret: str) -> "Secret":
        secret = secret.replace(" ", "").upper()
        padding = len(secret) % 8
        if padding:
            secret = secret + "=" * (8 - padding)
        return Secret(base64.b32decode(secret))

    @classmethod
    def from_hex(cls, secret: str) -> "Secret":
        return Secret(bytes.fromhex(secret))

    def to_int_list(self) -> List[int]:
        return list(self.secret)

    def to_base32(self) -> str:
        return base64.b32encode(self.secret).decode("ascii")

    def to_hex(self) -> str:
        return self.secret.hex()

    def to_bytes(self) -> bytes:
        return self.secret

    def __str__(self) -> str:
        return self.to_hex()

    def __eq__(self, other: Any) -> bool:
        return other is not None and isinstance(other, self.__class__) and self.secret == other.secret

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __len__(self) -> int:
        return len(self.secret)
