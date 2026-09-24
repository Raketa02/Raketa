"""The bcrypt adapter hashes at the work factor it is given, and verifies at any.

The cost is read off each hash rather than trusted from the constructor, because
the hash is where bcrypt records the cost it actually used.
"""

import pytest

from app.core.config import PRODUCTION_BCRYPT_ROUNDS
from app.modules.auth.infrastructure.password_hasher import BcryptPasswordHasher
from tests.unit.bcrypt_cost import BCRYPT_MINIMUM_ROUNDS, cost_of

#: Past bcrypt's seventy-two-byte limit, so the adapter pre-hashes it and stores
#: the result under its `sha256$` prefix. That is a second hashing path, and a
#: work factor honoured on one of them and not the other is the bug to catch.
LONG_PASSWORD = "p" * 100


@pytest.mark.parametrize("password", ["hunter22!", LONG_PASSWORD])
def test_a_hash_carries_the_work_factor_it_was_given(password) -> None:
    """The minimum rather than production's, because bcrypt's own default is
    production's — an adapter that ignored the argument would pass at twelve."""
    hasher = BcryptPasswordHasher(rounds=BCRYPT_MINIMUM_ROUNDS)

    assert cost_of(hasher.hash(password)) == BCRYPT_MINIMUM_ROUNDS


@pytest.mark.parametrize("password", ["hunter22!", LONG_PASSWORD])
def test_a_hash_made_at_production_strength_verifies_under_the_minimum(
    password,
) -> None:
    """Every hash stored before a setting was lowered keeps working after it.

    The direction that matters: a laptop's database seeded at production's cost,
    then a test configuration at the minimum. The other direction is the same
    `checkpw` and would prove nothing further.
    """
    stored = BcryptPasswordHasher(rounds=PRODUCTION_BCRYPT_ROUNDS).hash(password)

    under_the_minimum = BcryptPasswordHasher(rounds=BCRYPT_MINIMUM_ROUNDS)

    assert under_the_minimum.verify(password, stored)
    assert not under_the_minimum.verify("wrong-password1", stored)
