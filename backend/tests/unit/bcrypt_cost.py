"""Read the work factor off a stored hash, the only place it is recorded.

A bcrypt hash is sixty characters — `$2b$`, two digits of cost, `$`, then salt
and digest — and it ends the stored string whatever the adapter put before it,
which is how a long password's `sha256$` prefix is stepped over without this
helper knowing the prefix exists.
"""

BCRYPT_HASH_LENGTH = 60

#: bcrypt's own floor — `bcrypt.gensalt` refuses anything lower — and the work
#: factor `conftest.py` gives the suite.
BCRYPT_MINIMUM_ROUNDS = 4


def cost_of(stored_hash: str) -> int:
    bcrypt_hash = stored_hash[-BCRYPT_HASH_LENGTH:]
    _, scheme, cost, _ = bcrypt_hash.split("$")
    assert scheme == "2b", f"not a bcrypt hash: {scheme!r}"
    return int(cost)
