"""Turning the answer into the response, and omitting what does not apply.

**Every omitted field is omitted here, by not being passed.** The routes are
declared ``response_model_exclude_unset=True``, so a field this module does not
name is absent from the JSON — which is the whole mechanism behind
``docs/adr/0106`` §4's first spelling. A field this module passes as ``None`` is
the *second* spelling and means a measured nothing.

**Nothing here computes.** The Fit, its terms, the concerns, the modifiers and
the reason codes all arrive decided; the card and the at-stake block arrive
attached. What is left is naming fields — and a renderer that did arithmetic
would be a second implementation of a domain rule in the one layer nobody tests
for it.

**Every route renders the record**, and that is what makes the round trip true by
construction rather than by a test that happens to pass. A shortlist, a deal and
a search read back a month later reach :func:`_candidate` with the same
type — a ``SearchCandidateRecord`` — so there is no shape a fresh response could
carry that a stored one could not reproduce. The two departures the round trip
allows itself are the whole of the difference between these three functions: a
row the live gates now withhold, and a photo link minted per response
(``docs/adr/0109``, ``docs/adr/0107``).

**A withheld row carries no person.** It is a different type, not a candidate
with holes: there is no ``player_id`` on it and no card, so a client cannot
resurrect somebody the product has agreed to stop showing, and a renderer cannot
leak one by forgetting a branch.
"""

from __future__ import annotations

from typing import Any

from app.kernel import InvariantViolated

from app.modules.matchmaking.application.read_back_search import ReadBackAnswer
from app.modules.matchmaking.application.run_deck_deal import DeckAnswer
from app.modules.matchmaking.application.run_shortlist_search import ShortlistAnswer
from app.modules.matchmaking.domain.prompts import RaisedPrompt
from app.modules.matchmaking.domain.relaxation import RungOffer
from app.modules.matchmaking.domain.searches import (
    InclusionReason,
    RecordedCard,
    SearchCandidateRecord,
    SearchRecord,
    SortOption,
)
from app.modules.matchmaking.presentation.schemas import (
    CandidateSchema,
    ConcernSchema,
    OptimisedFor,
    PlayerCardSchema,
    PoolSchema,
    PromptSchema,
    RungOfferSchema,
    SearchEnvelope,
    ShortlistResponse,
    WireInclusionReason,
    WithheldRowSchema,
)


def render(answer: ShortlistAnswer) -> ShortlistResponse:
    """The whole response, from the record the use case just wrote.

    Every row is live by construction — the gates were evaluated moments ago —
    so ``withheld`` is not passed at all, and the field does not appear.
    """

    return ShortlistResponse(
        search=_envelope(
            answer.record, answer.sorts_available, prompts=answer.prompts
        ),
        candidates=[_candidate(row) for row in answer.record.returned],
    )


def render_deal(answer: DeckAnswer) -> ShortlistResponse:
    """One deal, in **the same shape a shortlist crosses in**.

    Not a shape of its own, and that is the read-back's requirement rather than
    tidiness: ``GET /searches/{id}`` returns the same schema the `POST` did, for
    any of the four surfaces, so a deal that crossed in a second shape would be a
    deal that could not be read back through the one renderer this module has.

    What differs is what the record says. ``mode`` is ``null`` — exactly on the
    deck and nowhere else — the sort list is empty, and ``rung_offers`` is
    ``null`` because the ladder does not reach here and the offers were not
    computed at all.

    ``prompts`` is not passed: a deal raises none, and the two spellings are
    different answers — this one is *the surface does not have them*, where an
    empty list would be *it ran them and found nothing*.
    """

    return ShortlistResponse(
        search=_envelope(answer.record, answer.sorts_available),
        candidates=[_candidate(row) for row in answer.record.returned],
    )


def render_read_back(answer: ReadBackAnswer) -> ShortlistResponse:
    """The same response, a month later, minus who we may no longer show.

    **The list keeps its length and its order.** A withheld row holds its place
    and says what happened to it; a row that still stands says so positively,
    because *we re-checked and this one is fine* is the other half of the
    statement and a client should not have to infer it from an absence.
    """

    return ShortlistResponse(
        search=_envelope(answer.record, answer.sorts_available),
        candidates=[
            WithheldRowSchema(withheld=True)
            if row.withheld
            else _candidate(row.recorded, withheld=False)
            for row in answer.rows
        ],
    )


def _envelope(
    record: SearchRecord,
    sorts: tuple[SortOption, ...],
    *,
    prompts: tuple[RaisedPrompt, ...] | None = None,
) -> SearchEnvelope:
    """The search's own facts, and the two that are about *now*.

    ``prompts`` is ``None`` for *do not mention it at all* — the read-back, where
    a month-old question would be asked about a value that has since moved — and
    a list on the `POST`, where an empty one honestly says the search raised
    none.
    """

    pool = record.pool_description
    fields: dict[str, Any] = {}
    if prompts is not None:
        fields["prompts"] = [_prompt(raised) for raised in prompts]
    return SearchEnvelope(
        search_id=record.id,
        at=record.at,
        surface=record.surface,
        mode=record.mode,
        ruleset_version=record.ruleset_version,
        engine_version=record.engine_version,
        # A shortlist optimises for the person who asked, always. The field is
        # on the envelope rather than implied by the surface because a line-up
        # with seats locked is the case where it is not, and one renderer should
        # read one fact.
        optimised_for=OptimisedFor.SEARCHER,
        index_stale=record.index_stale,
        pool=PoolSchema(
            sport=pool.sport,
            radius_km_used=pool.radius_km_used,
            players_in_range=pool.players_in_range,
            window=pool.window,
            post_gate=pool.post_gate,
        ),
        radius_clamp=record.radius_clamp_bit,
        sorts_available=list(sorts),
        # **`None` and an empty list are different answers.** `None` is *the
        # offers were not computed at all*; `[]` is *computed, and there is
        # nothing left to offer* — which is the honest empty state, where the
        # pool description beside it is the whole of what can be said.
        rung_offers=(
            None
            if record.rung_offers is None
            else [_offer(offer) for offer in record.rung_offers]
        ),
        **fields,
    )


def _offer(offer: RungOffer) -> RungOfferSchema:
    """One rung as it crosses. The payload field its ask does not use is omitted,
    not sent as null: a radius rung has no slot, rather than a slot of nothing."""

    fields: dict[str, Any] = {
        "rung": offer.rung,
        "ask": offer.ask,
        "candidates_above_floor": offer.candidates_above_floor,
        "window": offer.window,
    }
    if offer.radius_km is not None:
        fields["radius_km"] = offer.radius_km
    if offer.slot is not None:
        fields["slot"] = offer.slot
    return RungOfferSchema.model_validate(fields)


def _prompt(raised: RaisedPrompt) -> PromptSchema:
    """One standing question, carrying only the value it is asking about."""

    fields: dict[str, Any] = {"prompt": raised.prompt}
    if raised.radius_km is not None:
        fields["radius_km"] = raised.radius_km
    if raised.slots:
        fields["slots"] = list(raised.slots)
    if raised.mode is not None:
        fields["mode"] = raised.mode
    return PromptSchema.model_validate(fields)


def _candidate(
    row: SearchCandidateRecord, *, withheld: bool | None = None
) -> CandidateSchema:
    """One recorded row on the wire.

    ``withheld`` is ``None`` for *do not mention it at all* — the `POST`, where
    every row is live by construction — and ``False`` on a read-back, where the
    gates were re-evaluated and this row still stands. It is never ``True`` here:
    a withheld row is a different type and never reaches this function.
    """

    card = row.card
    if card is None:  # pragma: no cover — the record's own invariant refuses one
        # A ``RETURNED`` row holds a card by construction: the biconditional on
        # ``SearchCandidateRecord`` says so, and a row whose card could not be
        # assembled was dropped before it was ever written. Refused in the
        # kernel's own shape rather than rendered with a hole where a person is.
        raise InvariantViolated("a returned row with no card reached the wire")
    fields: dict[str, Any] = {
        "player_id": row.player_id,
        "fit": row.fit,
        "player_card": _card(card),
        "concerns": [ConcernSchema(term=term) for term in row.concerns],
        # The same mappings the record stores. One serialiser, two consumers:
        # the wire validates it into the discriminated union and the store keeps
        # it opaque, so the published shape and the stored blob cannot drift into
        # disagreeing about a field name.
        "terms": [dict(term) for term in row.terms],
        "degraded_terms": list(row.degraded_terms),
        "modifiers": [dict(modifier) for modifier in row.modifiers],
        "liveness_reasons": list(row.liveness_reasons),
    }
    if row.distance_km is not None:
        # Omitted rather than sent as zero when the term stood down, which is
        # what lets *Closest* sort a stood-down row last instead of first.
        fields["distance_km"] = row.distance_km
    if row.inclusion_reason is InclusionReason.INTEREST_LIFT:
        # **Only a reason that admits somebody crosses**, and the test is the
        # value rather than its presence: the store holds three and two of them
        # merely reorder. `NEWCOMER_WINDOW` reaches the client as a Liveness
        # reason instead, and `ZERO_EXPOSURE` never crosses at all — *nobody has
        # been shown them all week* is a third party's unpopularity.
        fields["inclusion_reason"] = WireInclusionReason.INTEREST_LIFT
    if row.at_stake is not None:
        fields["at_stake"] = {
            "win_delta": row.at_stake.win_delta,
            "loss_delta": row.at_stake.loss_delta,
        }
    if withheld is not None:
        fields["withheld"] = withheld
    return CandidateSchema.model_validate(fields)


def _card(card: RecordedCard) -> PlayerCardSchema:
    """The card as it was shown, from the row that recorded it.

    ``counted_games`` is never passed: the games ledger has no provider in this
    build, so the field does not apply and a zero would be an invented one.

    It takes a card and never an absence, so *a row with no person on it* is not
    a state this function has to have an opinion about.
    """

    fields: dict[str, Any] = {
        "nickname": card.nickname,
        "area_code": card.area_code,
        "social_tags": list(card.social_tags),
        "level": card.level,
        "band": card.band,
    }
    if card.photo_id is not None:
        fields["photo_id"] = card.photo_id
    return PlayerCardSchema.model_validate(fields)
