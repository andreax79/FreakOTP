#!/usr/bin/env python
# Prepare a test db generating random tokens

from freakotp.cli import FreakOTP, TokenType
from freakotp.secret import Secret
from pathlib import Path
from random import Random

if __name__ == "__main__":
    random = Random(5)
    words = Path('tests/words.txt').read_text().split('\n')
    filename = 'tests/test.db'
    freakotp = FreakOTP(filename=Path(filename))
    freakotp.token_db.truncate()

    for i in range(0, 20):
        issuer = random.choice(words)
        label = random.choice(words)
        secret = Secret.from_int_list([random.randint(0, 255) for _ in range(0, 16)])
        print(secret)
        freakotp.add_token(
            issuer=issuer,
            type= TokenType.TOTP if i % 4 else TokenType.HOTP,  # 1 in 4 is HOTP
            label=label,
            secret=secret
        )
