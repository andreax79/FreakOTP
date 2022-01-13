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

import os
import sys
import math
import json
import time
import hmac
import struct
import hashlib
import argparse
import base64
import urllib.parse

__author__ = 'Andrea Bonomi <andrea.bonomi@gmail.com>'
__version__ = '2.0.0'
__all__ = [
    'FreakOTP',
    'Token',
    'DEFAULT_PERIOD',
    'DEFAULT_ALGORITHM',
    'DEFAULT_DIGITS',
    'DEFAULT_FILENAME',
]

if sys.version_info <= (3, 0):
    print('Python 2 is vintage. Please use Python 3.')
    sys.exit(1)

ALGORITHMS = {
    'SHA1': hashlib.sha1,
    'SHA256': hashlib.sha256,
    'SHA512': hashlib.sha512,
    'MD5': hashlib.md5,
}

DEFAULT_PERIOD = 30
DEFAULT_ALGORITHM = 'SHA1'
DEFAULT_DIGITS = 6
DEFAULT_FILENAME = os.path.join(
    os.environ.get('APPDATA')
    or os.environ.get('XDG_CONFIG_HOME')
    or os.path.join(os.environ['HOME'], '.config'),
    'freeotp-backup.json',
)

TOTP = 'TOTP'
HOTP = 'HOTP'
SECURID = 'SecurID'


class Token(object):
    def __init__(self, data=None, uri=None):
        if data is not None:
            self.data = data
            self.type = data.get('type')
            self.algorithm = data.get('algo') or DEFAULT_ALGORITHM
            self.counter = data.get('counter')
            self.digits = data.get('digits') or DEFAULT_DIGITS
            self.issuer_int = data.get('issuerInt')
            self.issuer_ext = data.get('issuerExt')
            self.issuer = self.issuer_int or self.issuer_ext
            self.label = data.get('label')
            self.period = data.get('period') or DEFAULT_PERIOD
            self.secret = bytes([(x + 256) % 256 for x in data['secret']])
        elif uri is not None:
            uri_components = urllib.parse.urlparse(uri)
            query = dict(urllib.parse.parse_qsl(uri_components.query))
            self.type = uri_components.netloc.upper()
            self.algorithm = query.get('algorithm') or DEFAULT_ALGORITHM
            self.counter = int(query.get('counter')) if 'counter' in query else 0
            self.digits = (
                int(query.get('digits')) if 'digest' in query else DEFAULT_DIGITS
            )
            if ':' in uri_components.path:
                self.issuer, self.label = uri_components.path.split(':', 1)
                self.issuer_int = self.issuer
                self.issuer_ext = self.issuer
            else:
                self.label = uri_components.path
                self.issuer = None
                self.issuer_int = None
                self.issuer_ext = None
            self.period = (
                int(query.get('period')) if 'period' in query else DEFAULT_PERIOD
            )
            self.secret = base64.b32decode(query.get('secret'))

    def calculate(self, value=None):
        if self.type == SECURID:
            from securid.jsontoken import JSONTokenFile

            return JSONTokenFile(data=self.data).get_token().now()
            return ''
        algorithm = ALGORITHMS.get(self.algorithm, hashlib.sha1)
        if value is None:
            if self.type == HOTP:  # HOTP
                value = self.counter
            else:  # TOTP
                value = time.time() / self.period
        t = struct.pack(">q", int(value))
        hmac_ = hmac.HMAC(self.secret, t, algorithm).digest()
        offset = hmac_[-1] & 0x0F
        code = struct.unpack('>L', hmac_[offset : offset + 4])[0]
        frmt = '{0:0%dd}' % self.digits
        return frmt.format((code & 0x7FFFFFFF) % int(math.pow(10, self.digits)))

    def to_json(self):
        "Return token as json"
        return json.dumps(self.data, indent=2)

    def to_uri(self):
        "Return token as otpauth uri"
        data = {}
        if self.algorithm:
            data['algorithm'] = self.algorithm
        if self.digits:
            data['digits'] = self.digits
        if self.period:
            data['period'] = self.period
        if self.type == HOTP and self.counter:
            data['counter'] = self.counter
        data['secret'] = base64.b32encode(self.secret)
        if self.issuer:
            label = self.issuer + ':' + self.label
        else:
            label = self.label
        query = urllib.parse.urlencode(data)
        return urllib.parse.urlunparse(
            ('otpauth', self.type.lower(), label, None, query, None)
        )

    def print_qrcode(self):
        "Print token as qrcode"
        import qrcode

        qr = qrcode.QRCode()
        qr.add_data(self.to_uri())
        qr.print_ascii()


class FreakOTP(object):

    filename = None
    data = None
    verbose = None

    def __init__(self, filename=DEFAULT_FILENAME, verbose=False):
        self.filename = filename
        self.verbose = verbose
        with open(self.filename, 'r') as f:
            self.data = json.loads(f.read())

    def menu(self):
        for i, item in enumerate(self.data['tokenOrder'], start=1):
            print('{0:2d}) {1}'.format(i, item))

    def list(self):
        for item in self.data['tokenOrder']:
            print(item)

    def prompt(self):
        try:
            choice = input('Please make a choice: ')
        except KeyboardInterrupt:
            return
        try:
            index = int(choice)
        except:
            return
        try:
            token = self.get_token(index)
        except KeyError:
            print('Not found')
        if self.verbose:
            print(token.to_json())
        print(token.calculate())

    def get_token(self, index):
        t = self.data['tokenOrder'][index - 1]
        t = t.split(':', 1)
        try:
            return [
                Token(data=x)
                for x in self.data['tokens']
                if x['issuerInt'] == t[0] and x['label'] == t[1]
            ][0]
        except:
            raise KeyError(index)

    def find(self, arg):
        result = []
        labels = [x.strip() for x in ([arg] if isinstance(arg, str) else arg)]
        for label in labels:
            if label.startswith('otpauth://'):
                result.append(Token(uri=label))
        for token in self.data['tokenOrder']:
            tmp = token.lower().strip()
            for label in labels:
                if label.lower() in tmp:
                    t = token.split(':', 1)
                    result.extend(
                        [
                            Token(data=x)
                            for x in self.data['tokens']
                            if x['issuerInt'] == t[0] and x['label'] == t[1]
                        ]
                    )
                    break
        return result

    def calculate(self, token, value=None):
        return Token(token).calculate(value=value)


def main():
    parser = argparse.ArgumentParser(
        description='FreakOTP is a command line two-factor authentication application.'
    )
    parser.add_argument(
        '-f',
        '--filename',
        dest='filename',
        help='freeotp-backup.json path (default: {0})'.format(DEFAULT_FILENAME),
        default=DEFAULT_FILENAME,
    )
    parser.add_argument(
        '-v', '--verbose', dest='verbose', action='store_true', help='verbose output'
    )
    parser.add_argument(
        '-ls', dest='list', action='store_true', help='display token list'
    )
    parser.add_argument(
        '--uri', dest='uri', action='store_true', help='generate uri for token'
    )
    parser.add_argument(
        '--qrcode', dest='qrcode', action='store_true', help='generate qrcode for token'
    )
    parser.add_argument('token', nargs='*')
    args = parser.parse_args()
    if not os.path.exists(args.filename):
        print(
            'File {0} not found. Please copy the FreeOTP backup in the given path.'.format(
                args.filename
            )
        )
        sys.exit(1)
    freak = FreakOTP(filename=args.filename, verbose=args.verbose)
    if args.token:
        for token in freak.find(args.token):
            if freak.verbose:
                print(token.to_json())
            if args.uri:
                print(token.to_uri())
            elif args.qrcode:
                token.print_qrcode()
            else:
                print(token.calculate())
    elif args.list:
        freak.list()
    else:
        freak.menu()
        freak.prompt()


if __name__ == "__main__":
    main()
