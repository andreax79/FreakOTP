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

__author__ = 'Andrea Bonomi <andrea.bonomi@gmail.com>'
__version__ = '1.0.0'
__all__ = [
    'FreakOTP',
    'DEFAULT_PERIOD',
    'DEFAULT_ALGORITHM',
    'DEFAULT_DIGITS',
    'DEFAULT_FILENAME',
]

if sys.version_info <= (3, 0):
    print('Python 2 is vintage. Please use Python 3.')
    sys.exit(1)

ALGORITHMS = {
    'SHA1':   hashlib.sha1,
    'SHA256': hashlib.sha256,
    'SHA512': hashlib.sha512,
    'MD5':    hashlib.md5
}

DEFAULT_PERIOD = 30
DEFAULT_ALGORITHM = 'SHA1'
DEFAULT_DIGITS = 6
DEFAULT_FILENAME = os.path.join(
    os.environ.get('APPDATA') or
    os.environ.get('XDG_CONFIG_HOME') or
    os.path.join(os.environ['HOME'], '.config'),
    'freeotp-backup.json'
)

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
        choice = input('Please make a choice: ')
        try:
            index = int(choice)
        except:
            return
        try:
            token = self.get_token(index)
        except KeyError:
            print('Not found')
        if self.verbose:
            print(json.dumps(token, indent=2))
        print(self.calculate(token))

    def get_token(self, index):
        t = self.data['tokenOrder'][index - 1]
        t = t.split(':', 1)
        try:
            return [x for x in self.data['tokens'] if x['issuerInt'] == t[0] and x['label'] == t[1]][0]
        except:
            raise KeyError(index)

    def find(self, label):
        result = []
        labels = [x.lower().strip() for x in ([label] if isinstance(label, str) else label)]
        for token in self.data['tokenOrder']:
            tmp = token.lower().strip()
            for label in labels:
                if label in tmp:
                    t = token.split(':', 1)
                    result.extend([x for x in self.data['tokens'] if x['issuerInt'] == t[0] and x['label'] == t[1]])
                    break
        return result

    def calculate(self, token, value=None):
        secret = bytes((x + 256) & 255 for x in token["secret"])
        algorithm = ALGORITHMS.get(token.get('algo', DEFAULT_ALGORITHM), hashlib.sha1)
        if value is None:
            if token.get('type') == 'HOTP': # HOTP
                value = token['counter']
            else: # TOTP
                period = token.get('period', DEFAULT_PERIOD)
                value = time.time() / period
        t = struct.pack(">q", int(value))
        hmac_ = hmac.HMAC(secret, t, algorithm).digest()
        offset = hmac_[-1] & 0x0f
        code = struct.unpack('>L', hmac_[offset:offset+4])[0]
        digits = token.get('digits', DEFAULT_DIGITS)
        frmt = '{0:0%dd}' % digits
        return frmt.format((code & 0x7fffffff) % int(math.pow(10, digits)))

def main():
    parser = argparse.ArgumentParser(description='FreakOTP is a command line two-factor authentication application.')
    parser.add_argument('-f', '--filename',
            dest='filename',
            help='freeotp-backup.json path (default: {0})'.format(DEFAULT_FILENAME),
            default=DEFAULT_FILENAME)
    parser.add_argument('-v', '--verbose',
            dest='verbose',
            action='store_true',
            help='verbose output')
    parser.add_argument('-ls',
            dest='list',
            action='store_true',
            help='display token list')
    parser.add_argument('token', nargs='*')
    args = parser.parse_args()
    if not os.path.exists(args.filename):
        print('File {0} not found. Please copy the FreeOTP backup in the given path.'.format(args.filename))
        sys.exit(1)
    freak = FreakOTP(filename=args.filename,verbose=args.verbose)
    if args.token:
        for token in freak.find(args.token):
            if freak.verbose:
                print(json.dumps(token, indent=2))
            print(freak.calculate(token))
    elif args.list:
        freak.list()
    else:
        freak.menu()
        freak.prompt()

if __name__ == "__main__":
    main()
