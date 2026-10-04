"""Where a one-time credential's randomness comes from.

**``secrets``, never ``random``**: a link token and a ticket are each a bearer
credential for setting somebody's password, so they are drawn from the
operating system's CSPRNG, and an adapter is the only place that draws them —
the domain derives the code from the token and hashes what it is given, and
could not reach the entropy source if it wanted to.
"""

from __future__ import annotations

import secrets
from typing import Final

#: 32 bytes: 256 bits, printed URL-safe in 43 characters.
_BYTES: Final = 32


class RandomCredentialSecrets:
    """``CredentialSecrets`` over the operating system's CSPRNG."""

    def mint(self) -> str:
        return secrets.token_urlsafe(_BYTES)
