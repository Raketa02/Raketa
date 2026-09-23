"""The attestation, as a type that cannot exist unless somebody answered.

ADR-0124 makes the platform adults only and puts the rule where accounts are
created rather than where candidates are generated. What is asserted here is the
whole of it: an attestation is one boolean, it is never a date of birth, and no
registration can be constructed without one.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.modules.users.domain.errors import AdultAttestationRequired
from app.modules.users.domain.events import UserRegistered
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import (
    AdultAttestation,
    Email,
    HashedPassword,
)
from app.shared.ids import new_uuid


def test_an_unanswered_question_is_refused_with_its_own_code():
    with pytest.raises(AdultAttestationRequired) as refusal:
        AdultAttestation(False)

    assert refusal.value.code == "adult_attestation_required"
    assert refusal.value.status_code == 400


def test_an_answer_that_is_not_an_answer_is_refused_too():
    # ``None`` is what a body that omitted the field would carry through a lenient
    # boundary. It is not a quieter *no*; it is nobody having been asked.
    with pytest.raises(AdultAttestationRequired):
        AdultAttestation(None)  # type: ignore[arg-type]


def test_the_attestation_is_the_only_thing_it_holds():
    # One boolean, and no second field anybody could later read an age out of.
    attestation = AdultAttestation(True)

    assert attestation.value is True
    assert vars(attestation) == {"value": True}


def test_registering_records_the_attestation_on_the_first_event():
    now = datetime.now(timezone.utc)
    user = User.register(
        user_id=new_uuid(),
        email=Email("ada@example.com"),
        password_hash=HashedPassword("hash"),
        attestation=AdultAttestation(True),
        occurred_at=now,
    )

    [registered] = user.pull_events()
    assert isinstance(registered, UserRegistered)
    assert registered.adult_attested is True


def test_the_refusal_is_the_only_way_false_is_reachable():
    # ``False`` is representable on the event, because a boolean is. It is not
    # *reachable*: this type refuses it before an event can be built, so no
    # stream can carry one. ``test_user_event_codec`` holds the other half —
    # that an absent field is ``None`` and never ``False``.
    with pytest.raises(AdultAttestationRequired):
        AdultAttestation(False)


def test_a_stream_written_before_the_question_existed_still_replays():
    # No backfill: an account created before this keeps no attestation, and
    # ``None`` says exactly that rather than inventing a claim nobody made. The
    # decode this stands for is asserted through the real codec in
    # ``test_user_event_codec``; what is asserted here is that the aggregate
    # rebuilds from such a stream at all.
    now = datetime.now(timezone.utc)
    registered = UserRegistered(
        user_id=new_uuid(),
        email="ada@example.com",
        password_hash="hash",
        authority="USER",
        is_admin=False,
        is_active=True,
        occurred_at=now,
    )

    assert registered.adult_attested is None
    assert User.from_history([registered]).email.value == "ada@example.com"
