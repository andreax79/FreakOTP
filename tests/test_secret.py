from freakotp.secret import Secret

SECRET1 = "31323334353637383930313233343536373839303132333435363738393031323334353637383930313233343536373839303132333435363738393031323334"
SECRET2 = "3132333435363738393031323334353637383930313233343536373839303132"


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
