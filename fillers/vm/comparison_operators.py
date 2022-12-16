"""
VM Comparison Operator Tests (via Yul): LT, GT, SLT, SGT.

TODO: transaction reverted if not enough gas for: GT, SLT, SGT
TODO: transaction reverted if not enough values on the stack: GT, SLT, SGT
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
    to_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op


def get_code_for_unsigned_comparison(opcode_name: str, val_1: str, val_2: str):
    """
    Return Yul source and byte code for use in both LT and GT opcode tests.
    """
    if opcode_name == "lt":
        opcode = "10"
    elif opcode_name == "gt":
        opcode = "11"
    elif opcode_name == "eq":
        opcode = "14"
    else:
        raise Exception("Unexpected opcode provided for unsigned comparison.")

    yul_source = Template(
        """
        {
            function f(a, b) -> c
            {
                c := 0
                if $opcode_under_test(a, b) { c := 1 }
            }
            sstore(0, f($val_1, $val_2))
        }
        """
    )
    if val_1 != val_2:
        bytecode = Template(
            """0x6017565b60008282 $opcode_under_test
                 15601157600190505b92915050565b602160 $val_2
                 60 $val_1 6003565b600055"""
        )
    else:
        bytecode = Template(
            """0x6017565b60008282 $opcode_under_test
                 15601157600190505b92915050565b602060 $val_2
                 80 6003565b600055"""
        )

    return (
        Yul(
            yul_source.substitute(
                opcode_under_test=opcode_name,
                val_1=int(val_1, 0),
                val_2=int(val_2, 0),
            )
        ),
        bytecode.substitute(
            opcode_under_test=opcode, val_1=val_1[2:], val_2=val_2[2:]
        ),
    )


# TODO: change decorator to @test_from("istanbul")
@test_from_until("berlin", "shanghai")
def test_lt_gt(fork):
    """
    Test basic functionality for the LT and GT opcodes for non-error cases.
    """
    env = Environment()

    pre = {TestAddress: Account(balance=1000000000000000000000)}
    post = {}

    addr_1 = to_address(0x100)
    balance = 1000000000000000000000

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        to=addr_1,
        gas_limit=100000,
        gas_price=10,
        protected=False,
    )

    test_cases = [
        ["lt", "0x00", "0x01", True],
        ["lt", "0x01", "0x02", True],
        ["lt", "0x00", "0x00", False],
        ["lt", "0x01", "0x01", False],
        ["lt", "0x01", "0x00", False],
        ["lt", "0x02", "0x01", False],
        ["gt", "0x00", "0x01", False],
        ["gt", "0x01", "0x02", False],
        ["gt", "0x00", "0x00", False],
        ["gt", "0x01", "0x01", False],
        ["gt", "0x01", "0x00", True],
        ["gt", "0x02", "0x01", True],
    ]

    for opcode, val_1, val_2, result in test_cases:
        name = f"test_{val_1}_{opcode}_{val_2}"
        (yul, bytecode) = get_code_for_unsigned_comparison(
            opcode, val_1, val_2
        )

        pre[addr_1] = Account(code=yul, storage={0: 0xFF}, balance=balance)
        post[addr_1] = Account(code=bytecode, storage={0: int(result)})

        yield StateTest(env=env, pre=pre, post=post, txs=[tx], name=name)


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
        """  # noqa: E501
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


@test_from_until("berlin", "shanghai")
def test_lt_tx_reverts_upon_error(fork):
    """
    Test that the LT opcode reverts if:
    - The stack does not contain 2 entries.
    - Insufficient gas is provided.
    """
    env = Environment()

    pre = {TestAddress: Account(balance=1000000000000000000000)}
    post = {}

    addr_1 = to_address(0x100)
    balance = 1000000000000000000000
    storage = {0: 1}

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        to=addr_1,
        gas_limit=100000,
        gas_price=10,
        protected=False,
    )

    # TODO: Testing via storage does not seem strict enough - if LT does not
    # cause the tx to revert, but later fails this will cause the test to pass,
    # but for the wrong reason (false negative). In particular, this is the
    # case for the insufficient gas test. Is there a better way?

    """
    Test Case 1: Call LT on an empty stack.

    Tx should revert; storage should remain unchanged.
    """
    name = "lt_reverts_tx_with_no_stack_entries"

    code = Op.LT + Op.PUSH1(2) + Op.PUSH1(0) + Op.SSTORE

    pre[addr_1] = Account(code=code, storage=storage, balance=balance)
    post[addr_1] = Account(code=code, storage=storage)

    yield StateTest(env=env, pre=pre, post=post, txs=[tx], name=name)

    """
    Test Case 2: Call LT with a stack with only 1 entry.

    Tx should revert; storage should remain unchanged.
    """
    name = "lt_reverts_tx_with_one_stack_entry"

    code = Op.PUSH1(1) + Op.LT + Op.PUSH1(2) + Op.PUSH1(0) + Op.SSTORE

    pre[addr_1] = Account(code=code, storage=storage, balance=balance)
    post[addr_1] = Account(code=code, storage=storage)

    yield StateTest(env=env, pre=pre, post=post, txs=[tx], name=name)

    """
    Test Case 3: Call LT with insufficient gas.

    Tx should revert; storage should remain unchanged.
    """
    name = "lt_reverts_tx_with_insufficient_gas"

    code = Op.PUSH1(0) + Op.PUSH1(1) + Op.LT
    code += Op.PUSH1(2) + Op.PUSH1(0) + Op.SSTORE

    pre[addr_1] = Account(code=code, storage=storage, balance=balance)
    post[addr_1] = Account(code=code, storage=storage)

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        to=addr_1,
        gas_limit=21006,
        gas_price=10,
        protected=False,
    )
    yield StateTest(env=env, pre=pre, post=post, txs=[tx], name=name)
