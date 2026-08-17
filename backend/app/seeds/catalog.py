"""Which addresses exist, and what state each one is in.

One account today. Breadth — a brand-new player, a completed assessment, a
barely-established rating — is #97's, and this file is the shape it grows into:
an account is **named for the state it represents**, so signing in as an address
is a statement about what you expect to see rather than a lookup in somebody's
notes.

The address is *derived* from that name rather than typed beside it, so the two
cannot drift. The domain is on a TLD RFC 2606 reserves and no registry will ever
sell: a seed account can never become a real mailbox, so a run pointed at the
wrong database cannot mail a stranger. Which of the four reserved TLDs, and why
it is not the one the ticket names, is on ``RESERVED_TLD`` below.

**The catalog is validated on import, through the domain's own value objects.**
An address the API would refuse is refused here, before a session is opened —
otherwise the failure lands halfway through a run, with some accounts written and
some not.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.kernel import Sport
from app.modules.users.domain.value_objects import Email, Nickname, RawPassword

#: A TLD RFC 2606 reserves: no registry will ever sell a name under it, so a
#: seed account can never become somebody's real mailbox.
#:
#: **`.example` rather than the `.test` the ticket asks for, and the reason is
#: measured rather than preferred.** RFC 2606 §2 reserves four TLDs in one
#: sentence — `.test`, `.example`, `.invalid`, `.localhost` — and the boundary
#: schemas refuse two of them. `LoginRequest.email` and `UserResponse.email` are
#: `pydantic.EmailStr`, which is `email-validator`, which refuses any address
#: whose TLD is in its special-use list: `arpa, invalid, local, localhost,
#: onion, test`. So a `.test` account is one **no client can sign in as** (422)
#: and one `/users/me` cannot even serialise (500) — which contradicts this
#: ticket's other acceptance criterion, that an API-level test authenticates as
#: it. `example` is not on that list, and is reserved by the same sentence.
#:
#: Widening the boundary schema is the alternative and was deliberately not
#: taken: it is a public API change made to suit a development tool, and it
#: would let `alice@localhost` register. Reported on #94 and #97 instead.
#:
#: `test_the_boundary_schemas_accept_every_seeded_address` is what keeps this
#: honest — if a future `email-validator` adds `example` to that list, the suite
#: says so by name rather than through a 422 nobody can explain.
RESERVED_TLD = ".example"

#: Unregistrable, and visibly not a real address.
SEED_EMAIL_DOMAIN = f"rakieta{RESERVED_TLD}"

#: One password for every seeded account, so a developer signing in as any of
#: them types the same thing. It is public by construction — it is in this file
#: — which is the whole reason `app/seeds/guard.py` exists.
SEED_PASSWORD = "rakieta-seed1"


@dataclass(frozen=True)
class SeedAccount:
    """One deterministic account: what it is called, and what state it is in.

    ``slug`` is the name of the *state*, and it is the only identifier here —
    the address and the nickname are derived from it. Carrying an address as its
    own field would let an account be called one thing and reachable at another,
    which is precisely the confusion a named catalog exists to remove.
    """

    slug: str
    sport: Sport
    description: str

    @property
    def email(self) -> str:
        return f"{self.slug}@{SEED_EMAIL_DOMAIN}"

    @property
    def nickname(self) -> str:
        return self.slug


ASSESSMENT_IN_PROGRESS = SeedAccount(
    slug="assessment-in-progress",
    sport=Sport.PADEL,
    description=(
        "A registered player with an onboarding assessment open at its first "
        "question and no rating yet — the state a resume flow is developed "
        "against."
    ),
)

#: Every account this system creates. One, deliberately: this ticket proves the
#: path end to end and #97 broadens it.
ACCOUNTS: tuple[SeedAccount, ...] = (ASSESSMENT_IN_PROGRESS,)


def _refuse_an_impossible_catalog() -> None:
    """Fail at import rather than part-way through a run.

    The value objects are the domain's own, so this asks the exact question the
    registration endpoint would ask — an address or nickname the API would reject
    cannot sit here waiting to break a seed run that has already written half of
    its accounts.
    """

    RawPassword(SEED_PASSWORD)

    if not SEED_EMAIL_DOMAIN.endswith(RESERVED_TLD):
        raise RuntimeError(
            f"seed accounts must be addressed on the reserved '{RESERVED_TLD}' "
            f"TLD, which cannot be registered. '{SEED_EMAIL_DOMAIN}' can be."
        )

    seen: set[str] = set()
    for account in ACCOUNTS:
        Email(account.email)
        Nickname(account.nickname)
        if account.slug in seen:
            raise RuntimeError(f"two seed accounts are named '{account.slug}'")
        seen.add(account.slug)


_refuse_an_impossible_catalog()
