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

TOKEN_COLUMNS = [
    "rowid",
    "type",
    "algo",
    "counter",
    "digits",
    "issuer_int",
    "issuer_ext",
    "label",
    "period",
    "exp_date",  # SecurID token expiration date
    "pin",  # SecurID token pin
    "serial",  # SecurID token serial
    "secret",
]
SQL_DROP_TABLE = "drop table token"
SQL_CREATE_TABLE = """
create table if not exists token (
    type text,
    algo text,
    counter integer,
    digits integer,
    issuer_int text,
    issuer_ext text,
    label text,
    period integer,
    exp_date date,
    pin date,
    serial text,
    secret text
)"""
SQL_INSERT = """
insert into token(type, algo, counter, digits, issuer_int, issuer_ext, label, period, exp_date, pin, serial, secret)
values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
SQL_DELETE = "delete from token where rowid=?"
SQL_SELECT_TOKENS = f"select {','.join(TOKEN_COLUMNS)} from token"
SQL_UPDATE = """
update token
set
    type=?,
    algo=?,
    counter=?,
    digits=?,
    issuer_int=?,
    issuer_ext=?,
    label=?,
    period=?,
    exp_date=?,
    pin=?,
    serial=?,
    secret=?
where rowid=?
"""
