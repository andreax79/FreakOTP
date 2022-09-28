from freakotp.secret import Secret
from freakotp.token import Token, TokenType

RFC4226_TEST_VECTORS = """
   Count    Hexadecimal    Decimal        HOTP
   0        4c93cf18       1284755224     755224
   1        41397eea       1094287082     287082
   2         82fef30        137359152     359152
   3        66ef7655       1726969429     969429
   4        61c5938a       1640338314     338314
   5        33c083d4        868254676     254676
   6        7256c032       1918287922     287922
   7         4e5b397         82162583     162583
   8        2823443f        673399871     399871
   9        2679dc69        645520489     520489
"""
SECRET = "3132333435363738393031323334353637383930"


def test_rfc4226_test_vectors():
    tests = [x.strip() for x in RFC4226_TEST_VECTORS.split("\n")]
    tests = [x.split() for x in tests if x]
    tests = [(int(x[0]), x[3]) for x in tests if x[0] != "Count"]

    secret = Secret.from_hex(SECRET)
    token = Token(type=TokenType.HOTP, algorithm="SHA1", digits=6, secret=secret)
    for test in tests:
        assert token.calculate(counter=test[0]) == test[1]

    for test in tests:
        token = Token(type=TokenType.HOTP, algorithm="SHA1", digits=6, secret=secret, counter=test[0])
        assert token.calculate() == test[1]

    for test in tests:
        token = Token(type=TokenType.HOTP, algorithm="SHA1", digits=6, secret=secret)
        assert token.calculate(counter=test[0]) == test[1]
