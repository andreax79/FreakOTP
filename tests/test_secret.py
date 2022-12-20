from freakotp.secret import Secret

SECRET1 = "31323334353637383930313233343536373839303132333435363738393031323334353637383930313233343536373839303132333435363738393031323334"
SECRET2 = "3132333435363738393031323334353637383930313233343536373839303132"
SECRET_WITH_SPACES1 = "ZAZA 6B6B XIXI 2Y2Y 2C2C R5R5 ITIT JGJG O4O4 E3E3 NINI DTZT QQQQ"
SECRET_WITH_SPACES2 = "zaza 6b6b xixi 2y2y 2c2c r5r5 itit jgjg o4o4 e3e3 nini dtzt qqqq"
SECRET_WITH_SPACES3 = "C832 0F07 C1BA 2E8D 6358 D0B4 28F6 3D44 D134 9926 771D C26C 9B6A 1A81 CF33 8421"
SECRET_WITH_SPACES4 = "c832 0f07 c1ba 2e8d 6358 d0b4 28f6 3d44 d134 9926 771d c26c 9b6a 1a81 cf33 8421"


def test_secrets():
    s1 = Secret.from_hex(SECRET1)
    i1 = s1.to_int_list()
    assert i1 == [
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        48,
        49,
        50,
        51,
        52,
    ]
    s2 = Secret.from_int_list(i1)
    assert str(s2) == s2.to_hex()
    assert s1.secret == s2.secret
    assert s1 == s2
    s3 = Secret.from_base32(s1.to_base32())
    assert s1.secret == s3.secret
    assert s1 == s3
    s4 = Secret.from_hex(SECRET2)
    assert s1 != s4
    assert s4.to_hex() == SECRET2
    assert str(s4) == s4.to_hex()


def test_secrets_with_spaces():
    s1 = Secret.from_base32(SECRET_WITH_SPACES1)
    assert len(s1) == 32
    s2 = Secret.from_base32(SECRET_WITH_SPACES2)
    assert len(s2) == 32
    assert s1 == s2
    s3 = Secret.from_hex(SECRET_WITH_SPACES3)
    assert s1 == s3
    s4 = Secret.from_hex(SECRET_WITH_SPACES4)
    assert s1 == s4
