"""
VM Comparison Operator Tests (via Yul): LT, GT, SLT, SGT.

TODO: EQ, ISZERO
"""

from string import Template

from ethereum_test_tools import (
    Account,
    Environment,
    StateTest,
    TestAddress,
    Transaction,
    Yul,
    test_from_until,
)


def get_yul_for_unsigned_comparison(opcode: str):
    """
    Return Yul source code for use in both LT and GT opcode tests.
    """
    if opcode not in ["lt", "gt"]:
        raise Exception("Unexpected opcode provided for yul source.")
    yul_source = Template(
        """
        {
            function f(a, b) -> c
            {
                c := 0xff
                if $opcode_under_test(a, b) { c := 1 }
            }
            sstore(0, f(0, 1))
            sstore(1, f(1, 2))
            sstore(2, f(0, 0))
            sstore(3, f(1, 1))
            sstore(4, f(1, 0))
            sstore(5, f(2, 1))
            return(0, 32)
        }
        """
    )
    return Yul(yul_source.substitute(opcode_under_test=opcode))


# TODO: change decorator to @test_from("istanbul")
@test_from_until("berlin", "shanghai")
def test_lt(fork):
    """
    Test LT opcode.
    """
    env = Environment()

    pre = {
        "0x1000000000000000000000000000000000000000": Account(
            balance=0x0BA1A9CE0BA1A9CE,
            code=get_yul_for_unsigned_comparison("lt"),
        ),
        TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE),
    }

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to="0x1000000000000000000000000000000000000000",
        gas_limit=500000,
        gas_price=10,
        protected=False,
    )

    post = {
        "0x1000000000000000000000000000000000000000": Account(
            code="""0x601b565b600060ff905082821015601557600
                      190505b92915050565b602560016000600356
                      5b6000556032600260016003565b600155603
                      e6000806003565b600255604a600180600356
                      5b6003556057600060016003565b600455606
                      4600160026003565b60055560206000f3""",
            storage={
                0x00: 0x01,
                0x01: 0x01,
                0x02: 0xFF,
                0x03: 0xFF,
                0x04: 0xFF,
                0x05: 0xFF,
            },
        ),
    }

    yield StateTest(env=env, pre=pre, post=post, txs=[tx])


# TODO: change decorator to @test_from("istanbul")
@test_from_until("berlin", "shanghai")
def test_gt(fork):
    """
    Test GT opcode.
    """
    env = Environment()

    pre = {
        "0x1000000000000000000000000000000000000000": Account(
            balance=0x0BA1A9CE0BA1A9CE,
            code=get_yul_for_unsigned_comparison("gt"),
        ),
        TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE),
    }

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to="0x1000000000000000000000000000000000000000",
        gas_limit=500000,
        gas_price=10,
        protected=False,
    )

    post = {
        "0x1000000000000000000000000000000000000000": Account(
            code="""0x601b565b600060ff905082821115601557600
                      190505b92915050565b602560016000600356
                      5b6000556032600260016003565b600155603
                      e6000806003565b600255604a600180600356
                      5b6003556057600060016003565b600455606
                      4600160026003565b60055560206000f3""",
            storage={
                0x00: 0xFF,
                0x01: 0xFF,
                0x02: 0xFF,
                0x03: 0xFF,
                0x04: 0x01,
                0x05: 0x01,
            },
        ),
    }

    yield StateTest(env=env, pre=pre, post=post, txs=[tx])


def get_yul_for_signed_comparison(opcode: str):
    """
    Return Yul source code for use in both SLT and GLT tests.
    """
    if opcode not in ["slt", "sgt"]:
        raise Exception("Unexpected opcode provided for yul source.")
    yul_source = Template(
        """
        {
            function f(a, b) -> c {
                c := 0xff
                if $opcode_under_test(a, b) { c := 1 }
            }

            let minus1 := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
            let minus2 := 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe
            let minus3 := 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd
            sstore(0, f(minus1, 0))
            sstore(1, f(minus3, minus2))
            sstore(2, f(0, 1))
            sstore(3, f(minus1, minus1))
            sstore(4, f(0, 0))
            sstore(5, f(1, 1))
            sstore(6, f(0, minus1))
            sstore(7, f(minus2, minus3))
            sstore(8, f(1, 0))

            return(0, 32)
        }
        """  # noqa
    )
    return Yul(yul_source.substitute(opcode_under_test=opcode))


# TODO: change decorator to @test_from("istanbul")
@test_from_until("berlin", "shanghai")
def test_slt(fork):
    """
    Test SLT opcode.
    """
    env = Environment()

    pre = {
        "0x1000000000000000000000000000000000000000": Account(
            balance=0x0BA1A9CE0BA1A9CE,
            code=get_yul_for_signed_comparison("slt"),
        ),
        TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE),
    }

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to="0x1000000000000000000000000000000000000000",
        gas_limit=500000,
        gas_price=10,
        protected=False,
    )

    post = {
        "0x1000000000000000000000000000000000000000": Account(
            code="""0x601b565b600060ff905082821215601557600190505b92915050565b7
                      fffffffffffffffffffffffffffffffffffffffffffffffffffffffff
                      ffffffff7ffffffffffffffffffffffffffffffffffffffffffffffff
                      ffffffffffffffffe7fffffffffffffffffffffffffffffffffffffff
                      fffffffffffffffffffffffffd60876000846003565b6000556092828
                      26003565b600155609f600160006003565b60025560aa83846003565b
                      60035560b66000806003565b60045560c26001806003565b60055560c
                      e8360006003565b60065560d981836003565b60075560e66000600160
                      03565b60085560206000f3
                 """,
            storage={
                0x00: 0x01,
                0x01: 0x01,
                0x02: 0x01,
                0x03: 0xFF,
                0x04: 0xFF,
                0x05: 0xFF,
                0x06: 0xFF,
                0x07: 0xFF,
                0x08: 0xFF,
            },
        ),
    }

    yield StateTest(env=env, pre=pre, post=post, txs=[tx])


# TODO: change decorator to @test_from("istanbul")
@test_from_until("berlin", "shanghai")
def test_sgt(fork):
    """
    Test SGT opcode.
    """
    env = Environment()

    pre = {
        "0x1000000000000000000000000000000000000000": Account(
            balance=0x0BA1A9CE0BA1A9CE,
            code=get_yul_for_signed_comparison("sgt"),
        ),
        TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE),
    }

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to="0x1000000000000000000000000000000000000000",
        gas_limit=500000,
        gas_price=10,
        protected=False,
    )

    post = {
        "0x1000000000000000000000000000000000000000": Account(
            code="""0x601b565b600060ff905082821315601557600190505b92915050565b7
                      fffffffffffffffffffffffffffffffffffffffffffffffffffffffff
                      ffffffff7ffffffffffffffffffffffffffffffffffffffffffffffff
                      ffffffffffffffffe7fffffffffffffffffffffffffffffffffffffff
                      fffffffffffffffffffffffffd60876000846003565b6000556092828
                      26003565b600155609f600160006003565b60025560aa83846003565b
                      60035560b66000806003565b60045560c26001806003565b60055560c
                      e8360006003565b60065560d981836003565b60075560e66000600160
                      03565b60085560206000f3
                 """,
            storage={
                0x00: 0xFF,
                0x01: 0xFF,
                0x02: 0xFF,
                0x03: 0xFF,
                0x04: 0xFF,
                0x05: 0xFF,
                0x06: 0x01,
                0x07: 0x01,
                0x08: 0x01,
            },
        ),
    }

    yield StateTest(env=env, pre=pre, post=post, txs=[tx])
