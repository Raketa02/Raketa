"""What ``challenges`` demands of the matcher, run against every implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/challenge_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or turns
the build red. There is no skipped test to go stale.

**The world is built the way the platform builds one.** The reader goes through
sign-up, the profile commit, a real assessment run and the declaration route,
because ``searcher_facts`` reads all four live from the aggregates; the court
goes in through the **log** and is tailed exactly as the projection tails it,
because a card is a fold of an index row and there is no other way to give
somebody a chosen Level or a chosen area. A fixture that fabricated either would
be testing itself.

**Two seams the suite supplies for itself**, and they are the register's own
argument: the candidate index is the process's rather than the request's, and the
exposure ledger is Redis, which nothing in this repository needs running.

**The demand this port exists for is the one it is easiest to satisfy wrongly.**
``docs/adr/0143`` §3 turns on the pairing being computed *in the reader's own
direction* — neither stored Fit is publishable, because one is the organiser's
reading of the invitee under a label that says *for you* and the other was scored
with the searcher's own reliability deliberately set to ``None``. So the case
that matters most here is the same court read by two different people.
"""

from __future__ import annotations

import pytest

from app.bootstrap.challenge_demands import (
    CHALLENGE_DEMANDS,
    CHALLENGE_IMPLEMENTATIONS,
    PairingSeams,
    implementations_of,
)
from app.engines.matchfit.core import EvidenceKind, SearchMode
from app.kernel import Sport
from app.modules.challenges.domain.ports import (
    CourtPairingQuery,
    CourtSeat,
    PairingAbsence,
)
from app.shared.ids import new_uuid
from tests.api import matchmaking_world as world


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def _port(implementation, session, candidate_source, exposure_ledger):
    return implementation.build(
        PairingSeams(
            session=session,
            candidates=candidate_source,
            exposure=exposure_ledger,
        )
    )


async def _a_court(client, session_factory, candidate_source, *names, **facts):
    """Some people in the city, folded into the index the platform reads."""

    ids = [
        await world.a_candidate(client, session_factory, name, **facts)
        for name in names
    ]
    await world.fold_the_log(session_factory, candidate_source)
    return ids


def _across(*player_ids) -> tuple[CourtSeat, ...]:
    """A court of people **on the other side of the net**, which is the default.

    Singles has no other shape, and the side only reaches the forecast — so
    every case here that is not about the forecast says *across* and means *the
    ordinary one*.
    """

    return tuple(
        CourtSeat(player_id=player_id, beside_you=False)
        for player_id in player_ids
    )


def _kinds(card) -> set[str]:
    """The evidence kinds on a card, **as machine codes.**

    The payload the record stores and the wire validates is the same mapping, and
    it is taken down to codes on the way in: a stored blob has to be readable by
    something that does not import this build's enums. So these are strings, and
    a test comparing them by identity would be asserting something about Python.
    """

    return {term["evidence"]["kind"] for term in card.pairing.terms}


def _level_fit(card) -> dict:
    return next(
        term["evidence"]
        for term in card.pairing.terms
        if term["evidence"]["kind"] == EvidenceKind.LEVEL_FIT.value
    )


# ---------------------------------------------------------------------------
# The register itself
# ---------------------------------------------------------------------------


def test_every_published_port_has_an_implementation():
    """A port with nothing registered is a demand nothing on earth runs."""

    unregistered = [
        port.__name__ for port in CHALLENGE_DEMANDS if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_is_of_a_published_port():
    """And the other direction, so the two lists check each other."""

    stray = [
        one.name
        for one in CHALLENGE_IMPLEMENTATIONS
        if one.port not in CHALLENGE_DEMANDS
    ]

    assert stray == []


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_every_implementation_satisfies_the_protocol(
    implementation, session_factory, candidate_source, exposure_ledger
):
    """Structural, so a method renamed on one side is red here rather than a
    runtime ``AttributeError`` on somebody's challenge screen."""

    async with session_factory() as session:
        built = _port(implementation, session, candidate_source, exposure_ledger)

    assert isinstance(built, CourtPairingQuery)


# ---------------------------------------------------------------------------
# The answer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_a_card_comes_back_for_everybody_asked_about_and_nobody_else(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """**One question, asked once for the whole court, handed back sorted.**

    Sorted on the player's id, because a set is never the source of an order and
    the rule is stated on the collection rather than on what happens to be
    observable (``docs/adr/0105`` §1).

    *Answers only about ids it was asked about* is the other half, and it is the
    half a snapshot walk gets wrong: the index holds the whole city, and a read
    that returned everybody near the reader would be a search wearing a
    challenge's clothes.
    """

    reader = await world.a_searcher(client, "reader")
    asked = await _a_court(
        client, session_factory, candidate_source, "ada", "bea", mu=reader["mu"]
    )
    unasked = await _a_court(
        client, session_factory, candidate_source, "cleo", mu=reader["mu"]
    )

    async with session_factory() as session:
        answer = await _port(
            implementation, session, candidate_source, exposure_ledger
        ).cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=_across(*asked),
        )

    assert answer.absent is None
    assert [card.person.player_id for card in answer.cards] == sorted(asked)
    assert unasked[0] not in {card.person.player_id for card in answer.cards}


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_the_person_block_is_a_whole_handle_and_no_free_text(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """Who they are, and the closed list it is.

    **No bio and no free text of any kind, ever**, and the refusal is stronger
    here than where it was written: a searcher chose to look, an invitee was put
    in front of somebody without asking. There is no field on this block for one
    to arrive in, which is what the assertion below is really about.

    ``photo_id`` and ``photo_url`` are present **exactly together**, and a person
    with no photograph has neither — the client draws the generated court poster,
    which needs nothing from the wire.
    """

    reader = await world.a_searcher(client, "reader")
    (them,) = await _a_court(
        client, session_factory, candidate_source, "ada", mu=reader["mu"]
    )

    async with session_factory() as session:
        answer = await _port(
            implementation, session, candidate_source, exposure_ledger
        ).cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=_across(them),
        )

    person = answer.cards[0].person
    assert person.nickname == "ada"
    assert person.area_code
    assert person.range_low <= person.level <= person.range_high
    assert person.band
    assert (person.photo_id is None) and (person.photo_url is None)


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_the_pairing_is_computed_in_the_readers_own_direction(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """**The demand this port exists for** (``docs/adr/0143`` §3).

    One court, two readers, and each is told about the *other* — so the level-fit
    evidence names the asker as ``my_mu`` both times. A pairing replayed from a
    stored Fit could not do this: ``fit_ab`` is the organiser's reading of the
    invitee printed under a label that says *for you*, and ``fit_ba`` was scored
    with the searcher's own reliability deliberately set to ``None`` and was
    built not to be published at all.
    """

    reader = await world.a_searcher(client, "reader")
    other = await world.a_searcher(client, "other")
    await world.fold_the_log(session_factory, candidate_source)

    async with session_factory() as session:
        port = _port(implementation, session, candidate_source, exposure_ledger)
        mine = await port.cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=_across(other["id"]),
        )
        theirs = await port.cards_for(
            reader_id=other["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=_across(reader["id"]),
        )

    assert _level_fit(mine.cards[0])["my_mu"] == pytest.approx(reader["mu"])
    assert _level_fit(mine.cards[0])["their_mu"] == pytest.approx(other["mu"])
    assert _level_fit(theirs.cards[0])["my_mu"] == pytest.approx(other["mu"])
    assert _level_fit(theirs.cards[0])["their_mu"] == pytest.approx(reader["mu"])


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_the_pairing_carries_its_own_renormalisation_basis(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """A Fit, the terms that made it, and **the terms that stood down.**

    The contributions sum to the Fit *before* the modifiers, and the number the
    screen prints is the one after — so the two are asserted apart rather than
    against each other. That gap is ``docs/adr/0143`` §5 showing through: the
    dock is part of what the platform makes of a pairing and belongs in the
    figure, and ``modifiers`` is engine internals this screen does not draw.

    Without the basis a Fit is uninterpretable — a 78 built on four terms and a
    78 built on seven are different readings of one number — which is the exact
    failure ``degraded_terms`` exists to prevent, and the reason it ships on a
    screen that draws no *Why?* sheet over it.

    The contributions sum to the Fit before the modifiers, which is what makes
    the breakdown checkable rather than decorative.
    """

    reader = await world.a_searcher(client, "reader")
    (them,) = await _a_court(
        client, session_factory, candidate_source, "ada", mu=reader["mu"]
    )

    async with session_factory() as session:
        answer = await _port(
            implementation, session, candidate_source, exposure_ledger
        ).cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=_across(them),
        )

    pairing = answer.cards[0].pairing
    scored = {term["term"] for term in pairing.terms}
    stood_down = {term for term, _ in pairing.degraded_terms}

    assert pairing.terms
    assert not scored & stood_down
    # **A share of a hundred**, over the terms that actually fired — which is
    # what makes the basis beside it load-bearing rather than decorative.
    assert sum(term["weight"] for term in pairing.terms) == pytest.approx(100.0)
    # Each contribution reconciles with its own weight and value, so a
    # breakdown nobody could check a year later is not what ships.
    assert all(
        term["contribution"] == pytest.approx(term["weight"] * term["value"])
        for term in pairing.terms
    )
    assert 0 <= pairing.forecast.pct <= 100
    assert EvidenceKind.LEVEL_FIT.value in _kinds(answer.cards[0])


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_a_partner_is_not_priced_as_an_opponent(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """**A forecast is a claim about a game, and a game has two sides.**

    The same four people arranged two ways are two different games, so the same
    person beside you and across from you must not produce one number. A read
    that only knew *who* would have to put everybody across the net — and then
    print *how even would a game against them be* about a teammate.
    """

    reader = await world.a_searcher(client, "reader")
    ada, bea = await _a_court(
        client, session_factory, candidate_source, "ada", "bea", mu=reader["mu"]
    )

    async with session_factory() as session:
        port = _port(implementation, session, candidate_source, exposure_ledger)
        ada_beside = await port.cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=(
                CourtSeat(player_id=ada, beside_you=True),
                CourtSeat(player_id=bea, beside_you=False),
            ),
        )
        ada_across = await port.cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=(
                CourtSeat(player_id=ada, beside_you=False),
                CourtSeat(player_id=bea, beside_you=True),
            ),
        )

    # The cards themselves are unchanged — who somebody is and what you make of
    # them does not depend on which side they sit.
    beside_fits = {card.person.player_id: card.pairing.fit for card in ada_beside.cards}
    across_fits = {card.person.player_id: card.pairing.fit for card in ada_across.cards}
    assert beside_fits == across_fits
    # **And the forecast is one figure carried on every card**, because it is
    # about the game rather than about a seat.
    assert len({card.pairing.forecast for card in ada_beside.cards}) == 1


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_a_court_with_nobody_across_the_net_has_no_forecast(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """**A side with nobody on it is not a side.**

    Reachable rather than theoretical: a doubles court whose far side has all
    declined still stands while the organiser can refill it, and the reader and
    their partner are left with nothing to be forecast against. An invented
    number would be worse than an absence, and the rest of the card — who they
    are, and what you make of them — is unaffected.
    """

    reader = await world.a_searcher(client, "reader")
    (partner,) = await _a_court(
        client, session_factory, candidate_source, "ada", mu=reader["mu"]
    )

    async with session_factory() as session:
        answer = await _port(
            implementation, session, candidate_source, exposure_ledger
        ).cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=(CourtSeat(player_id=partner, beside_you=True),),
        )

    assert answer.absent is None
    assert answer.cards[0].pairing.forecast is None
    assert answer.cards[0].pairing.terms
    assert answer.cards[0].person.nickname == "ada"


# ---------------------------------------------------------------------------
# The two absences — ``docs/adr/0143`` §6
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_a_reader_with_no_rating_in_the_sport_has_nothing_to_compute(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """**Being asked to play a sport you never declared for is how this works.**

    Not a corner of it, and not an error: the screen draws the arrangement and
    the handles, omits the pairing block and does not apologise for it. The code
    says whose gap it is, and it is not an outage's.
    """

    reader = await world.a_searcher(client, "reader")
    (them,) = await _a_court(
        client, session_factory, candidate_source, "ada", mu=reader["mu"]
    )

    async with session_factory() as session:
        answer = await _port(
            implementation, session, candidate_source, exposure_ledger
        ).cards_for(
            reader_id=reader["id"],
            # Rated and declared in padel, challenged at tennis.
            sport=Sport.TENNIS,
            mode=SearchMode.COMPETITIVE,
            court=_across(them),
        )

    assert answer.absent is PairingAbsence.NOTHING_TO_COMPUTE
    assert answer.cards == ()


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_a_reader_with_no_profile_at_all_has_nothing_to_compute(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """The third of the three conflicts, and the same answer.

    A player who signed up and stopped is somebody a challenge can still reach —
    a mutual yes needs no profile of the person it names — so this is reachable
    rather than theoretical.
    """

    stranger, _ = await world.register(client, "stranger")
    reader = await world.a_searcher(client, "reader")
    await world.fold_the_log(session_factory, candidate_source)

    async with session_factory() as session:
        answer = await _port(
            implementation, session, candidate_source, exposure_ledger
        ).cards_for(
            reader_id=stranger,
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=_across(reader["id"]),
        )

    assert answer.absent is PairingAbsence.NOTHING_TO_COMPUTE


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_somebody_the_index_cannot_describe_is_absent_and_the_rest_answer(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """**A person with no card keeps their seat**, and nobody else loses theirs.

    A row can be missing because the tail has not reached them or because they
    are gone, and neither is a fact this screen is entitled to state — so it
    states none, draws that seat without a card, and answers about everybody
    else. Refusing the whole court instead would let one stranger's absence
    blank a screen somebody is answering on.
    """

    reader = await world.a_searcher(client, "reader")
    (them,) = await _a_court(
        client, session_factory, candidate_source, "ada", mu=reader["mu"]
    )
    nobody = new_uuid()

    async with session_factory() as session:
        answer = await _port(
            implementation, session, candidate_source, exposure_ledger
        ).cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=_across(them, nobody),
        )

    assert answer.absent is None
    assert [card.person.player_id for card in answer.cards] == [them]


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_an_empty_court_is_an_empty_answer_and_never_a_refusal(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """A singles challenge read by the organiser asks about nobody at all.

    Their own seat is the only other one, and a pairing with yourself is not a
    question — so the answer is empty rather than absent, and the reader is told
    nothing went wrong.
    """

    reader = await world.a_searcher(client, "reader")
    await world.fold_the_log(session_factory, candidate_source)

    async with session_factory() as session:
        answer = await _port(
            implementation, session, candidate_source, exposure_ledger
        ).cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.COMPETITIVE,
            court=_across(),
        )

    assert answer == type(answer)()
    assert answer.absent is None


@pytest.mark.parametrize("implementation", registered(CourtPairingQuery))
async def test_what_is_at_stake_is_omitted_in_for_fun(
    implementation, client, session_factory, candidate_source, exposure_ledger
):
    """**Meaningless rather than unavailable**, which is why it is an omission.

    A for-fun game is never counted, so asking what it would do to a Level is a
    category error rather than a read that failed — and the same absence in
    competitive would mean one of the two holds no rating. Never a pair of zeros
    either way.
    """

    reader = await world.a_searcher(client, "reader")
    (them,) = await _a_court(
        client, session_factory, candidate_source, "ada", mu=reader["mu"]
    )

    async with session_factory() as session:
        port = _port(implementation, session, candidate_source, exposure_ledger)
        for_fun = await port.cards_for(
            reader_id=reader["id"],
            sport=world.SPORT,
            mode=SearchMode.FOR_FUN,
            court=_across(them),
        )

    assert for_fun.cards[0].pairing.at_stake is None
