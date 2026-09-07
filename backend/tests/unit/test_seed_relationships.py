"""The eleven relationships: what they declare, and the ways a run refuses them.

**A distribution cannot assert a pair.** Five of the ten `LivenessSignal` codes
are facts about two people, and the layer this file covers is what exhibits them
— so what is checked here is the half that can be checked without a database:
the declarations, and every refusal that fires before a session is opened.

The other half — the edges written through the use cases and the claims read back
off the protagonist's own screens — is in `test_seed_cohort.py`, because it needs
a seeded world and is one assertion about one run.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.bootstrap.composition import build_ruleset
from app.kernel import Sport
from app.modules.challenges.domain.seats import SeatAnswer
from app.seeds import relationships
from app.seeds.catalog import ACCOUNTS, PROTAGONISTS, RatedRun, RatingClaim
from app.seeds.cohort import COHORT
from app.seeds.pairs import _assign, _enough_organisers, _every_rung_has_a_witness
from app.seeds.relationships import (
    ABSENT_ON_THE_BLOCKED_GATE,
    ABSENT_ON_THE_OPEN_CHALLENGE_GATE,
    PROTAGONIST,
    RELATIONSHIP_ACCOUNTS,
    RELATIONSHIPS,
    OnTheirCourt,
    TheyChallengedYou,
    members_who_carry_an_inbox,
    members_who_might_organise,
)

# ---------------------------------------------------------------------------
# 1. The declarations
# ---------------------------------------------------------------------------


def test_there_are_eleven_and_each_is_named_for_the_pair():
    """The catalog names an account for its **own state**; this file names one
    for a **relationship**, from the protagonist's side.

    A pool card is read constantly and a sign-in happens once, so the second
    person is *you* and the protagonist is named in the description rather than
    in the slug. The rule is checked because it is the one thing that separates
    these eleven from a second catalog of ordinary accounts.
    """

    assert len(RELATIONSHIPS) == 11
    for relationship in RELATIONSHIPS:
        slug = relationship.account.slug
        assert "you" in slug, slug
        assert PROTAGONIST.slug in relationship.account.description, slug


def test_only_one_protagonist_carries_relationships():
    """Decision 11, kept honest. *You* is unambiguous only while it names one
    account, and a second protagonist acquiring edges is the day the naming rule
    is revisited — in the open, rather than by a slug quietly becoming a riddle.
    """

    assert PROTAGONIST in PROTAGONISTS
    for other in PROTAGONISTS:
        if other is PROTAGONIST:
            continue
        assert other.slug not in {
            account.slug for account in RELATIONSHIP_ACCOUNTS
        }


def test_every_account_is_rated_in_every_sport_its_claim_touches():
    """The refinement a naive absence fixture does not have.

    An account gated for an **accidental** reason is absent, and an absence claim
    passes: `NOT_RATED` is the third gate and `OPEN_CHALLENGE` is the fifth, so a
    relationship account with no padel rating would be missing from the pool for
    a reason that has nothing to do with its edge.
    """

    for relationship in RELATIONSHIPS:
        rated = {
            scenario.sport
            for scenario in relationship.account.scenarios
            if isinstance(scenario, RatedRun)
        }
        assert Sport.PADEL in rated, relationship.account.slug
        sport = getattr(relationship.edge, "sport", None)
        if sport is not None:
            assert sport in rated, relationship.account.slug


def test_the_one_account_on_another_sport_is_the_outgoing_challenge():
    """**Tennis is the only sport doing work here, and it is doing all of it.**

    Every other edge is padel, which keeps the claims comparable. The outgoing
    challenge is on tennis because that is the only way *one open challenge per
    pair, across sports* becomes observable: that person is gated out of her
    **padel** pool by a **tennis** challenge, which is the rule's entire content.
    """

    elsewhere = {
        relationship.account.slug
        for relationship in RELATIONSHIPS
        if getattr(relationship.edge, "sport", Sport.PADEL) is not Sport.PADEL
    }
    assert elsewhere == {"you-challenged-them"}


def test_the_two_co_invitees_differ_by_seat_state():
    """Only a fixture proves that two screens differ.

    The court draws a filled seat and an unanswered one side by side, and two
    co-invitees answering alike would prove one of them twice.
    """

    answers = [
        relationship.edge.answer
        for relationship in RELATIONSHIPS
        if isinstance(relationship.edge, OnTheirCourt)
    ]
    assert sorted(answers, key=str) == sorted([SeatAnswer.ACCEPTED, None], key=str)


def test_the_absences_are_named_per_gate_and_do_not_overlap():
    """The claim is the **gate histogram**, so each absence names one code.

    An account counted against two gates would make the histogram unreadable:
    it is first-in-declaration-order, so a candidate lands on exactly one.
    """

    challenged = {r.account.slug for r in ABSENT_ON_THE_OPEN_CHALLENGE_GATE}
    blocked = {r.account.slug for r in ABSENT_ON_THE_BLOCKED_GATE}
    assert not challenged & blocked
    assert len(challenged) == 4
    assert len(blocked) == 2


# ---------------------------------------------------------------------------
# 2. The refusals, at import
# ---------------------------------------------------------------------------


def test_a_co_invitee_nobody_seats_is_refused(monkeypatch):
    """A seat naming nobody is a send that would be refused half way through a
    run, with the court sent and the answers never given."""

    court = next(
        relationship
        for relationship in RELATIONSHIPS
        if isinstance(relationship.edge, TheyChallengedYou)
    )
    monkeypatch.setattr(
        relationships,
        "RELATIONSHIPS",
        tuple(
            replace(relationship, edge=replace(relationship.edge, co_invitees=()))
            if relationship is court
            else relationship
            for relationship in RELATIONSHIPS
        ),
    )

    with pytest.raises(RuntimeError, match="co-invitee nobody seats"):
        relationships._refuse_an_impossible_layer()


def test_an_edge_on_a_sport_the_account_is_not_rated_in_is_refused(monkeypatch):
    """The accidental-exclusion trap, refused before a session is opened."""

    monkeypatch.setattr(
        relationships,
        "RELATIONSHIPS",
        tuple(
            replace(
                relationship,
                account=replace(
                    relationship.account,
                    scenarios=(
                        RatedRun(
                            sport=Sport.PADEL,
                            answers=relationship.account.scenarios[0].answers,
                            claim=RatingClaim(band="Established"),
                        ),
                    ),
                ),
            )
            if relationship.account.slug == "you-challenged-them"
            else relationship
            for relationship in RELATIONSHIPS
        ),
    )

    with pytest.raises(RuntimeError, match="holds no TENNIS rating"):
        relationships._refuse_an_impossible_layer()


def test_two_accounts_at_one_slug_are_refused(monkeypatch):
    monkeypatch.setattr(
        relationships, "RELATIONSHIPS", RELATIONSHIPS + (RELATIONSHIPS[0],)
    )

    with pytest.raises(RuntimeError, match="two seed accounts are named"):
        relationships._refuse_an_impossible_layer()


def test_a_name_the_catalog_already_uses_is_refused(monkeypatch):
    """**The check spans both lists**, because the runner walks both through one
    registration and an address is derived from a slug.

    Within either list alone the collision is invisible, and the run would meet
    it half way through at the second registration for one address — with the
    first half of the accounts already written.
    """

    stolen = replace(
        RELATIONSHIPS[0],
        account=replace(RELATIONSHIPS[0].account, slug=ACCOUNTS[0].slug),
    )
    monkeypatch.setattr(
        relationships, "RELATIONSHIPS", (stolen,) + RELATIONSHIPS[1:]
    )

    with pytest.raises(RuntimeError, match=f"named '{ACCOUNTS[0].slug}'"):
        relationships._refuse_an_impossible_layer()


# ---------------------------------------------------------------------------
# 3. The inboxes CHALLENGE_LOAD's three rungs are borne by
# ---------------------------------------------------------------------------


def test_the_loaded_and_the_organisers_are_disjoint():
    """A member cannot fill their own inbox, and the rule says so rather than
    the writer discovering it as a refusal about challenging yourself."""

    loaded = {member.handle for member in members_who_carry_an_inbox()}
    organisers = {member.handle for member in members_who_might_organise()}
    assert len(loaded) == relationships.LOADED_INBOXES
    assert not loaded & organisers
    assert organisers == {
        member.handle for member in COHORT.members
    } - loaded


def test_an_inbox_is_covered_only_when_every_rung_has_its_own_witness():
    """Three inboxes of eight leave `SOME` and `BUSY` without a witness.

    A card prints the **deepest** rung it reaches and nothing else, so an *at
    least* test over the thresholds would call three deep inboxes covered while
    two of the three codes have never been drawn anywhere.
    """

    rungs = build_ruleset().liveness.challenge_load_rungs
    depths = sorted(rung.at_least for rung in rungs)

    assert _every_rung_has_a_witness(depths, rungs)
    assert not _every_rung_has_a_witness([max(depths)] * len(depths), rungs)
    assert not _every_rung_has_a_witness(depths[:-1], rungs)


def test_the_organiser_count_is_matched_deepest_to_deepest():
    """A different question, asked of different numbers: **how many people could
    put a seat in each inbox**, where one open challenge per pair makes an
    organiser worth exactly one seat."""

    assert _enough_organisers([3, 5, 8], [3, 5, 8])
    assert _enough_organisers([9, 4, 6], [3, 5, 8])
    assert not _enough_organisers([8, 8, 2], [3, 5, 8])
    assert not _enough_organisers([8, 8], [3, 5, 8])


def test_the_deepest_rung_goes_to_whichever_inbox_the_most_can_reach():
    """Who gets which depth is decided by what the searches found.

    One open challenge per pair means a rung of eight needs eight distinct
    organisers who can each see that member — so writing the assignment down
    would be a fixture that discovers on the day that one of them cannot.
    """

    loaded = members_who_carry_an_inbox()
    reachable = {
        loaded[0].handle: ["a", "b", "c"],
        loaded[1].handle: [f"o{index}" for index in range(9)],
        loaded[2].handle: ["p", "q", "r", "s", "t"],
    }
    plan = _assign(
        loaded,
        [3, 5, 8],
        reachable,
        {member.handle: 0 for member in loaded},
    )

    assert len(plan[loaded[1].handle]) == 8
    assert len(plan[loaded[2].handle]) == 5
    assert len(plan[loaded[0].handle]) == 3


def test_an_inbox_that_is_already_deep_enough_is_not_topped_up():
    """The run that creates nothing is the run that matters, so a standing depth
    is subtracted rather than ignored — a second `make seed` sends nothing."""

    loaded = members_who_carry_an_inbox()
    reachable = {member.handle: [f"o{i}" for i in range(9)] for member in loaded}
    plan = _assign(
        loaded,
        [3, 5, 8],
        reachable,
        {loaded[0].handle: 8, loaded[1].handle: 5, loaded[2].handle: 1},
    )

    assert plan[loaded[0].handle] == []
    assert plan[loaded[1].handle] == []
    assert len(plan[loaded[2].handle]) == 2
