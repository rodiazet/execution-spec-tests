"""
Test SWAP opcodes.
"""

from ethereum_test_tools import (
    Account,
    Environment,
    StateTest,
    Transaction,
    test_from_until,
    to_address,
)


# TODO: change decorator to @test_from("istanbul")
@test_from_until("istanbul", "shanghai")
def test_swap(fork):
    """
    Test SWAP1-SWAP16 opcodes.
    Based on:
     - ethereum/tests:
        src/GeneralStateTestsFiller/VMTests/vmTests/swapFiller.yml
        by: Ori Pomerantz qbzzt1@gmail.com
     - ethereum/execution-spec-tests:
        fillers/vm/dup.py
        by Mario Vega
    """
    env = Environment()
    pre = {
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(
            balance=1000000000000000000000
        )
    }
    txs = []
    post = {}

    """
    We are setting up 16 accounts, ranging from 0x100 to 0x10f.
    They push values into the stack from 0-32, but each contract uses a
    different SWAP opcode, and depending on the opcode used, the items copied
    into the storage changes.
    """
    for i in range(0, 16):
        """
        Account 0x100 uses SWAP1,
        ...
        Account 0x10f uses SWAP16.
        """
        account = to_address(0x100 + i)
        swap_opcode = 0x90 + i

        pre[account] = Account(
            code=(
                # Push 0 - 16 onto the stack
                """0x6000 6001 6002 6003 6004 6005 6006 6007 6008 6009
                         600A 600B 600C 600D 600E 600F 6010"""
                +
                # Use the SWAP opcode for this account
                hex(swap_opcode)[2:]
                +
                # Save each stack value into different keys in storage
                """6000 55 6001 55 6002 55 6003 55 6004 55 6005 55
                       6006 55 6007 55 6008 55 6009 55 600A 55 600B 55
                       600C 55 600D 55 600E 55 600F 55 6010 55"""
            )
        )

        """
        Also we are sending one transaction to each account.
        The storage of each will only change by two items: storage[0]
        and storage[i].
        The value depends on the SWAP opcode used.
        """
        tx = Transaction(
            ty=0x0,
            nonce=i,
            to=account,
            gas_limit=500000,
            gas_price=10,
            protected=False,
            data="",
        )
        txs.append(tx)

        """
        SWAP1 swaps the 1st element (0x10) of the stack with the 2nd (0x0F).
        SWAP16 swaps the 1st element (0x10) of the stack with the 17th (0x00).

        The storage will be structured as follows:

        0x00: 0x0F, 0xOE,... ,0x00 (Depending on SWAP opcode)
        0x01: 0x10 for account 0x100; 0x0F otherwise
        0x02: 0x10 for account 0x101; 0x0E otherwise
        0x03: 0x10 for account 0x102; 0x0D otherwise
        0x04: 0x10 for account 0x103; 0x0C otherwise
        0x05: 0x10 for account 0x104; 0x0B otherwise
        0x06: 0x10 for account 0x105; 0x0A otherwise
        0x07: 0x10 for account 0x106; 0x09 otherwise
        0x08: 0x10 for account 0x107; 0x08 otherwise
        0x09: 0x10 for account 0x108; 0x07 otherwise
        0x0A: 0x10 for account 0x109; 0x06 otherwise
        0x0B: 0x10 for account 0x10A; 0x05 otherwise
        0x0C: 0x10 for account 0x10B; 0x04 otherwise
        0x0D: 0x10 for account 0x10C; 0x03 otherwise
        0x0E: 0x10 for account 0x10D; 0x02 otherwise
        0x0F: 0x10 for account 0x10E; 0x01 otherwise
        0x10: 0x10 for account 0x10F; 0x00 otherwise

        Or, alternatively represented per account:

        0x100: 0x0F, 0x10, Ox0E, 0x0D, 0x0C, 0x0B, 0x0A, 0x09, ..., 0x01, 0x00
        0x101: 0x0E, 0x0F, Ox10, 0x0D, 0x0C, 0x0B, 0x0A, 0x09, ..., 0x01, 0x00
        0x102: 0x0D, 0x0F, Ox0F, 0x10, 0x0C, 0x0B, 0x0A, 0x09, ..., 0x01, 0x00
        0x103: 0x0C, 0x0F, Ox0E, 0x0D, 0x10, 0x0B, 0x0A, 0x09, ..., 0x01, 0x00
        ...
        ...
        0x10D: 0x02, 0x0F, Ox0E, ..., 0x06, 0x05, 0x04, 0x03, 0x10, 0x01, 0x00
        0x10E: 0x01, 0x0F, Ox0E, ..., 0x06, 0x05, 0x04, 0x03, 0x02, 0x10, 0x00
        0x10F: 0x00, 0x0F, Ox0E, ..., 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0x10
        """
        keys = range(17)
        values = list(range(16, -1, -1))
        values[0], values[i + 1] = values[i + 1], values[0]
        s = dict(zip(keys, values))

        post[account] = Account(storage=s)

    yield StateTest(env=env, pre=pre, post=post, txs=txs)
