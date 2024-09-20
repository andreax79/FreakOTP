# FreakOTP
FreakOTP is a command line two-factor authentication application. Tokens can be imported from FreeOTP.

[![Build Status](https://github.com/andreax79/freakotp/workflows/Tests/badge.svg)](https://github.com/andreax79/freakotp/actions)
[![PyPI version](https://badge.fury.io/py/freakotp.svg)](https://badge.fury.io/py/freakotp)
[![PyPI](https://img.shields.io/pypi/pyversions/freakotp.svg)](https://pypi.org/project/freakotp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Known Vulnerabilities](https://snyk-widget.herokuapp.com/badge/pip/freakotp/badge.svg)](https://snyk.io/test/github/andreax79/freakotp)

Requirements
-----------
* Python 3.6+

Install
-------

```
pip install freakotp
```

Screencast
----------

[![asciicast](https://asciinema.org/a/1GMjswJnFTU66ffc8uj8Rc3Ex.svg)](https://asciinema.org/a/1GMjswJnFTU66ffc8uj8Rc3Ex)

## Usage

The commands included in `freakotp` are as follows:

```bash
$ frakotp --help
Usage: freakotp [OPTIONS] [COMMAND|[TOKENS]...] [ARGS]...

  FreakOTP is a command line two-factor authentication application.

Options:
  --version                       Show the version and exit.
  --db PATH                       Database path.
  -v, --verbose                   Verbose output.
  -c, --counter INTEGER           HOTP counter value.
  -t, --time [%Y-%m-%dT%H:%M:%S]  TOTP timestamp.
  --copy / --no-copy              Copy the code into the clipboard.
  --help                          Show this message and exit.

Commands:
  .add     Import a new token into the database
  .delete  Delete tokens
  .edit    Edit tokens
  .export  Export tokens
  .help    Show help and exit
  .import  Import tokens from backup
  .ls      Display token list
  .otp     Display OTPs
  .qrcode  Display token qrcodes
  .uri     Display token uri
```

All the commands start with a dot, e.g. `.add`, `.delete`, `.ls`.
To view the help of any of the commands, add `--help`, example:

```bash
$ freakotp .add --help
Usage: freakotp .add [OPTIONS]

  Import a new token into the database

  Example: freaktop .add

Options:
  --type [TOTP|HOTP|SECURID]      Token type
  -a, --algorithm [SHA1|SHA256|SHA512|MD5]
                                  Algorithm
  -c, --counter INTEGER           HOTP counter value
  -d, --digits INTEGER            Number of digits in one-time password
  -i, --issuer TEXT               Issuer
  -l, --label TEXT                Label
  -p, --period INTEGER            Time-step duration in seconds
  -s, --secret TEXT               Secret key Base32
  -u, --uri TEXT                  URI (otpauth://)
  --help                          Show this message and exit.
```

Then invoked without argument, `freakotp` will launch interactive gui.
You can generate OTP code from existing token, adding new token or delete existing one.

```
$ freakotp
ENTER Show OTP  ^C Exit  ^Q QR-Code  ^U URI  ^I Insert  ^O Edit  ^X Delete
>  1: roof:toll
   2: mental:suggestion
   3: congress:originally
   4: inspired:petroleum
   5: design:meal
   6: contribute:loop
   7: official:care
   8: rapacious:vote
   9: tumble:discredit
  10: perch:safe
  11: array:depend
  12: firm:spoken
  13: advice:reduction
  14: adhere:fill
  15: indication:assistance
  16: pompous:security
  17: illuminate:hydroxyl
  18: spar:enrich
  19: patronage:characteristic
  20: built:atom
  20/20
>
```

Using the interactive gui:

- **UP** / **PG UP** / **DOWN** / **PG DOWN** to move cursor up and down
- **ENTER** to display OTP code of the selected token
- **CTRL-C** / **ESC** to exit
- **CTRL-Q** diplay the selected token QR Code
- **CTRL-U** export the selected token as URI
- **CTRL-I** add a new token
- **CTRL-O** edit the selected token
- **CTRL-X** delete the selected token

Without a command, `freakotp` generates the OTP codes for the matching tokens and
copies the first code into the clipboard.

```
$ freakotp.py loop
074324
```

### freakotp .add

The `freakotp .add` command adds a new token to the databases.
The token can be added from an otpauth:// URI or individual fields.

```
$ freakotp.py .add                                                                                                                                                         2 ↵
Add token
URI (otpauth://):
Token type (TOTP, HOTP, SECURID) [TOTP]:
Algorithm (SHA1, SHA256, SHA512, MD5) [SHA1]:
Number of digits in one-time password [6]:
Issuer: example
Label: loop
Time-step duration in seconds [30]:
Secret key: JOXI2L47UKOFUKCMT33VEGBJZ4
Token added
$ freakotp .ls -l loop
  21 TOTP    SHA1    6  30 example:loop
```

### freakotp .otp

The `freakotp .otp` command generates the OTP codes for the matching tokens (by default all tokens).

```
$ freakotp .otp
181715 roof:toll
893942 mental:suggestion
159412 congress:originally
062913 inspired:petroleum
277466 design:meal
574172 contribute:loop
919814 official:care
834047 rapacious:vote
402014 tumble:discredit
942488 perch:safe
154642 array:depend
833406 firm:spoken
080836 advice:reduction
088928 adhere:fill
165262 indication:assistance
522675 pompous:security
561630 illuminate:hydroxyl
881838 spar:enrich
949880 patronage:characteristic
906287 built:atom
$ freakotp .otp -l at
873564     15 TOTP    SHA1    6  30 indication:assistance
561630     17 HOTP    SHA1    6  30 illuminate:hydroxyl
450645     19 TOTP    SHA1    6  30 patronage:characteristic
173862     20 TOTP    SHA1    6  30 built:atom
```

### freakotp .delete

The `freakotp .delete` command delete all matching tokens.

```
$ .delete array firm
Delete token
Do you want to remove array:depend ? [y/N]: n
Do you want to remove firm:spoken ? [y/N]: y
Token deleted
```

### freakotp .edit

The `freakotp .edit` command edit all matching tokens.

```
$ .edit mental:suggestion
Edit token mental:suggestion
Secret [KESEPY2AIMAAE23OKRKZJIDFNA======]:
Issuer [mental]:
Label [suggestion]:
Token type: TOTP
Algorithm: SHA1
Number of digits in one-time password [6]:
Time-step duration in seconds [30]:
Token updated
```

### freakotp .export

The `freakotp .export` command generates a tokens backup in FreakOTP/FreeOTP format.

```
$ freakotp .export --filename freakotp.json
12 tokens exported
```

### freakotp .import

The `freakotp .import` command import the tokens from a FreakOTP/FreeOTP backup.
The `--delete-existing-data` options delete all the existing token before importing the backup.

```
$ freakotp .import --filename freakotp.json --delete-existing-data
7 tokens imported
```

### freakotp .ls

The `freakotp .ls` command lists the tokens.
The `--long` options enable the long listing format (token id, type (TOTP/HOTP), algorithm, digits, period, name).

```
$ freakotp .ls --long
   1 HOTP    SHA1    6  30 roof:toll
   2 TOTP    SHA1    6  30 mental:suggestion
   3 TOTP    SHA1    6  30 congress:originally
   4 TOTP    SHA1    6  30 inspired:petroleum
   5 HOTP    SHA1    6  30 design:meal
   6 TOTP    SHA1    6  30 contribute:loop
   7 TOTP    SHA1    6  30 official:care
   8 TOTP    SHA1    6  30 rapacious:vote
   9 HOTP    SHA1    6  30 tumble:discredit
  10 TOTP    SHA1    6  30 perch:safe
  11 TOTP    SHA1    6  30 array:depend
  12 TOTP    SHA1    6  30 firm:spoken
  13 HOTP    SHA1    6  30 advice:reduction
  14 TOTP    SHA1    6  30 adhere:fill
  15 TOTP    SHA1    6  30 indication:assistance
  16 TOTP    SHA1    6  30 pompous:security
  17 HOTP    SHA1    6  30 illuminate:hydroxyl
  18 TOTP    SHA1    6  30 spar:enrich
  19 TOTP    SHA1    6  30 patronage:characteristic
  20 TOTP    SHA1    6  30 built:atom
```

### freakotp .qrcode

The `freakotp .qrcode` command displ use a long listing formatays the QR Codes of the matching tokens.

```
$ freakotp .qrcode atom
built:atom
    █▀▀▀▀▀█ █▄▄▄▀█▀ ▄▀█▀   ▄▀▄▄ ▄▀▀▀▀ █▀▀▀▀▀█
    █ ███ █ ▄▄█▄▄▄▄  ▀ █▄▄▀ ▀▀▄  ▀▀▀█ █ ███ █
    █ ▀▀▀ █  ███▄▀█ █▄▄█ ▀  █▄ ▀ ▄▄██ █ ▀▀▀ █
    ▀▀▀▀▀▀▀ █▄█ ▀ ▀▄▀▄█▄▀ ▀▄▀ █ ▀▄█ ▀ ▀▀▀▀▀▀▀
    ▀▄▀█ █▀▀▄█▀█   ▀▄▀██▄█▄█    ▄█▄▄  █ ▄█▄▀█
    ▀▀▄▀ █▀█▄▄▀█▀ ▀▄ ▀ ▄█ █▀▀█   ▀█ ▀▄  ▀▀ ▄▀
    ▀▀▄███▀▀▄██ █▄▄▄ ▀  █ █▀▀▀██▄▄▄▀██▀  █▀ █
    ██▀▄ ▀▀█▄▀█▀██ █▄▄ ▀▀ ▄ █▀▄█▄▀ ▄ ▀▀ ██ ▀▀
     ▀▄█ ▄▀██     █▀  ▄ ▄█▄▀ █ ██ █ ██ ▄▀ ▄ ▀
    ▄▄▄▀█▄▀▄▄█▄▀▀  █▄▄█▀▄▄▀██▀ ▀▄  ▄██▀█▀██▄
    █▀█▄██▀█▀▀██▀▄▄▄█▄ █ ▄ █ ██  █▄█▄▀█▀ ▀▀▄█
    █▄██▄▄▀▀▀  ▄▄  ▄▀▀█ █ ████▄ █ █▄▀ ▄▀▄▀▀█
    ▀▀ ▄█▄▀▄▄ ▄█▄▄ ▄▄██▄▀ ▄ █▀████▄██▀▄█ █▄▀
    █ █▀▀ ▀▀█▀▄▀ ▄▄   ▀▀▀██ ▀▀▀ ▄▀ ▀ █▀█ █ ▄█
    ▀█▀▀▀█▀▄▄▀  ▀▄ ▄▄ █▄█▀ ███ ▀ ▀▀▀█▄█▄▀▀  ▀
    ▀  █ █▀█▀ ▄█▀▀▀ █ ██  ▀▀█  ▀▀█▀ ▀  ▀▄██ ▄
     ▀▀ ▀ ▀ ▄▀ ▄ █ ▀ ▄▄ ██▀▄▄▄▄ ▄▀█▄█▀▀▀██▀▄█
    █▀▀▀▀▀█ ██ █ ▀▄▄█▄▀█▀   █ ▀ ▀▄▀▀█ ▀ █▄▀█
    █ ███ █ ▄▄▀    ▀▄▄ ███▄▀█▀▄▀▄██ ▀█▀████ ▀
    █ ▀▀▀ █ ▀█ █ ███▄▀█▀██▀ █  ▄▀ █ ▄  ▀▄███▀
    ▀▀▀▀▀▀▀ ▀▀       ▀ ▀▀▀▀ ▀▀ ▀  ▀▀▀  ▀  ▀▀
````


### freakotp .uri

The `freakotp .uri` command exports the matching tokens as URI.

```
$ freakotp .uri atom
otpauth://totp/built:atom?algorithm=SHA1&digits=6&period=30&secret=72UU5WIYEN2YQKZABWVNWI6P7E%3D%3D%3D%3D%3D%3D
```

Environment Variables
---------------------

By default `freakotp` stores your tokens inside a `$HOME/.config/FreakOTP/freakotp.db`
directory on Linux or macOS, or inside your user profile folder on Windows.

To alter this, you can use the `FREAKOTP_DB` environment variable to use a different
path for storing your tokens.

```bash
export FREAKOTP_DB=~/Private/FreakOTP/freakotp.db
```

Licence
-------
MIT

Links
-----

* [FreeOTP](https://github.com/freeotp)
* [pzp](https://github.com/andreax79/pzp)
* [Pure python QR Code generator](https://github.com/lincolnloop/python-qrcode)
* [Black, The Uncompromising Code Formatter](https://github.com/psf/black)
