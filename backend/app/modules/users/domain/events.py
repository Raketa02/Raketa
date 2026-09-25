from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class UserRegistered:
    """An account opened — with credentials, and **unnamed**.

    Carries no nickname since ``docs/adr/0171`` §2: sign-up is email, password
    and the Adult attestation, and the name and nickname arrive together in
    :class:`UserNamed`. The contract stays ``users.user_registered`` / v1
    because a version exists to tell two stored shapes apart and only one will
    ever be stored — only ``local`` runs, its store is disposable and a reset
    seed is the migration. The day a store outlives a change like this, the
    version is the first thing that has to move.
    """

    user_id: UUID
    email: str
    password_hash: str
    authority: str
    is_admin: bool
    is_active: bool
    occurred_at: datetime
    # Appended after ``occurred_at`` because it carries a default: a stream
    # written before the question was asked decodes with it, and adds no
    # migration. The contract stays ``users.user_registered`` / v1 — the field
    # is additive and every reader that never mentions it is unaffected.
    #
    # **Three values, and the third is not a quieter no.** ``True`` is the
    # attestation; ``None`` is an account registered before this existed, and
    # says only that nobody was asked. Backfilling those to ``False`` would
    # invent the very fact the attestation exists to record (``docs/adr/0124``).
    # ``False`` is unreachable on the write path — ``AdultAttestation`` refuses
    # it before an event can be built — and is kept representable only because a
    # boolean is.
    #
    # It is a claim of adulthood and **never a date of birth**: nothing
    # downstream asks how old, and the candidate index fails its build if a date
    # ever appears.
    adult_attested: Optional[bool] = None


@dataclass(frozen=True)
class UserNamed:
    """The naming — one act, both values (``docs/adr/0171`` §2).

    A **Name** and a **Nickname** together, because they are asked under one
    title and a later change is the same act: the fold keeps the latest. There
    is no event for one without the other.
    """

    user_id: UUID
    name: str
    nickname: str
    occurred_at: datetime


@dataclass(frozen=True)
class UserDisabled:
    user_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class UserPromotedToAdmin:
    user_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class UserMarkedAsTester:
    """The account now carries the **tester mark** (``docs/adr/0180`` §9).

    A mark and not a role: ``Authority`` does not move, because being shown a
    feature early grants no power over anyone. Set by an admin command and never
    by the player, and read by the player app as ``is_tester`` on its own
    account — which it hands to flag evaluation, so that no datafile ever has
    to name a tester.
    """

    user_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class UserUnmarkedAsTester:
    """The tester mark cleared. Its own event rather than the mark carrying a
    boolean, so the stream says *who was a tester, and when* in the words it
    was done in (``docs/adr/0180`` §9)."""

    user_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class PasswordChanged:
    """A new password, and the instant every older session stopped counting.

    **Carries the new hash**, as ``UserRegistered`` carries the first
    (``docs/adr/0185`` §7): a password is chosen by its holder and lives as long
    as the account, so the stream that records the account records it — which
    is a different thing from the one-time credential that may have opened the
    way to it, which never enters an event (``docs/adr/0184`` §4).

    ``occurred_at`` **is the credentials-changed instant**: projected onto the
    ``users`` row, it refuses every access token issued before it. There is no
    field saying how the password was changed, because nothing reads one.
    """

    user_id: UUID
    password_hash: str
    occurred_at: datetime
