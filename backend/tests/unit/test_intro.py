"""The intro: one line a player writes, fenced at the write against contact.

``docs/adr/0170`` §2 — the moderation story is a rule at the write, and the
fence is contact. Every refusal here is reproduced by a line a player could
type, because the rule's whole worth is what it lets through and what it does
not: *a rule that lets a phone number through is the worse failure and is the
one the tests exist for.*

**The write path refuses; the fold accepts.** ``written`` is what the commit
runs and ``recorded`` is what a replay runs, and the second re-checks nothing —
the cap is a number product may move, and a stream is a record of what happened.
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated
from app.modules.player_profile.domain.errors import IntroNotAdmitted, IntroRefusal
from app.modules.player_profile.domain.intro import INTRO_MAX_CHARACTERS, Intro


def refused(text: str) -> IntroRefusal:
    with pytest.raises(IntroNotAdmitted) as caught:
        Intro.written(text)
    return caught.value.reason


# ---------------------------------------------------------------------------
# What is admitted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        "Moved from Wrocław in May. Needs opponents.",
        "Three sets, best of five",
        # A number that dials nothing is not a phone number.
        "Three sets, 100 zł to the winner",
        "Two games in. Moved here in September, still learning the city.",
        # Any language — nothing here reads English.
        "Gram od zeszłego roku, szukam sparingpartnera na wieczory.",
        "Perfect attendance. Brings the shuttles & a friend.",
    ],
)
def test_a_line_about_oneself_is_admitted_verbatim(line: str) -> None:
    intro = Intro.written(line)

    assert intro is not None
    assert intro.text == line


def test_a_line_is_trimmed_and_the_trimmed_line_is_what_is_kept() -> None:
    intro = Intro.written("  Will travel for a hard game.  \n")

    assert intro is not None
    assert intro.text == "Will travel for a hard game."


@pytest.mark.parametrize("blank", [None, "", "   ", "\n\t "])
def test_nothing_but_whitespace_is_absent_rather_than_an_empty_intro(
    blank: str | None,
) -> None:
    """A player who skips has no intro — not an empty one (``docs/adr/0170`` §1)."""

    assert Intro.written(blank) is None


def test_exactly_the_cap_is_admitted() -> None:
    """The cap is 250 (``docs/adr/0200`` §9), up from 100 (``docs/adr/0170``
    §4): spelled here as the number, so a change to the constant is a change
    somebody reads."""

    line = "x" * INTRO_MAX_CHARACTERS

    intro = Intro.written(line)

    assert intro is not None and len(intro.text) == 250


# ---------------------------------------------------------------------------
# The shape
# ---------------------------------------------------------------------------


def test_one_character_over_the_cap_is_too_long() -> None:
    assert refused("x" * (INTRO_MAX_CHARACTERS + 1)) is IntroRefusal.TOO_LONG


def test_the_cap_is_counted_after_trimming() -> None:
    padded = "   " + "x" * INTRO_MAX_CHARACTERS + "   "

    intro = Intro.written(padded)

    assert intro is not None and len(intro.text) == INTRO_MAX_CHARACTERS


@pytest.mark.parametrize(
    "line",
    [
        "Moved here in May.\nNeeds opponents.",
        "Moved here in May.\r\nNeeds opponents.",
        "Moved here in May.\u2028Needs opponents.",
    ],
)
def test_any_line_break_is_multiline(line: str) -> None:
    assert refused(line) is IntroRefusal.MULTILINE


# ---------------------------------------------------------------------------
# The fence: contact
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        "WhatsApp me 600 123 456",
        "Call +48 600-123-456 after six",
        "Text 6001234567",
        "Ring (022) 123 45 67",
        # Digits spaced out one by one are still a number to dial, and so are
        # digits spaced out by more than one character.
        "6 0 0 1 2 3 4 5 6",
        "600  123  456",
        "600 - 123 - 456",
        "600/123/456",
        "600_123_456",
        "600, 123, 456",
        "600–123–456",
        # Full-width digits normalise to the digits they are, and a zero-width
        # space between every digit is invisible on a card and no separator.
        "Zadzwoń ６００１２３４５６",
        "6\u200b0\u200b0\u200b1\u200b2\u200b3\u200b4\u200b5\u200b6",
    ],
)
def test_a_phone_shaped_run_of_digits_is_contact(line: str) -> None:
    assert refused(line) is IntroRefusal.CONTAINS_CONTACT


@pytest.mark.parametrize(
    "line",
    [
        "Write to karol@example.com",
        "karol.nowak@gmail.com for games",
        # Half an address is still an address.
        "karol@gmail",
        "Find me on insta @karol_plays",
        "@karol",
    ],
)
def test_an_email_or_a_handle_is_contact(line: str) -> None:
    assert refused(line) is IntroRefusal.CONTAINS_CONTACT


@pytest.mark.parametrize(
    "line",
    [
        "Book me at https://karol.example.com",
        "http://bit.ly/karol",
        "www.karolplays.pl",
        "karolplays.pl — all my times are there",
        "wa.me/48600123456",
        "t.me/karol",
        # A path after it makes it an address whatever its case.
        "Padel.Co/karol",
    ],
)
def test_a_url_or_a_bare_domain_is_contact(line: str) -> None:
    assert refused(line) is IntroRefusal.CONTAINS_CONTACT


@pytest.mark.parametrize(
    "line",
    [
        # A stray at-sign with nothing to name is not a handle.
        "Meet @ the club bar after",
        # An abbreviation is not a domain.
        "Play most evenings, e.g. Tuesday and Thursday.",
        # A score is not a phone number.
        "Lost 6-4 6-3 last week, back for more",
        "Back on court since 2019",
        # Two years with a dash between them are a career, not a number.
        "Played league 2015-2022 in Kraków, back for more",
        "Klub 2019–2024, teraz wolny strzelec",
        # A missing space after a full stop is a typo, not a site under `.in`.
        "Moved here in May.In the evenings I play padel.",
    ],
)
def test_the_fence_is_about_contact_and_not_about_punctuation(line: str) -> None:
    assert Intro.written(line) is not None


def test_a_score_line_with_enough_digits_is_refused_and_that_is_the_cost() -> None:
    """The digit rule's named false positive (``docs/adr/0170``, consequences):
    eight digits across two badminton games read as a number to dial, where a
    three-set tennis score stays under the seven. Pinned so the trade is a fact
    and not a surprise — and so that loosening it is a decision made against
    refusals rather than a guess."""

    assert refused("Badminton 21-19 21-17 last night") is IntroRefusal.CONTAINS_CONTACT
    assert Intro.written("Won 6-4 7-6 6-3 in the final") is not None


def test_a_lowercase_run_on_under_a_known_tld_is_refused_and_that_is_the_cost() -> None:
    """The bare-domain rule reads lowercase only, so *May.In* passes as a typo
    while *may.in* does not — a false refusal, costing a rewrite, on the side
    the ADR says to err on. Pinned so the trade is a fact and not a surprise."""

    assert refused("moved here in may.in the evenings") is IntroRefusal.CONTAINS_CONTACT


def test_the_reason_crosses_as_the_refusals_details() -> None:
    """One code, one coarse reason — the client says what to change and the
    server never explains what it matched (``docs/adr/0170`` §2)."""

    with pytest.raises(IntroNotAdmitted) as caught:
        Intro.written("WhatsApp me 600 123 456")

    assert caught.value.code == "intro_not_admitted"
    assert caught.value.details == {"reason": "contains_contact"}


# ---------------------------------------------------------------------------
# Where it crosses
# ---------------------------------------------------------------------------


def test_the_intro_reaches_the_record_and_its_author_and_nowhere_else() -> None:
    """``docs/adr/0170`` §3 — *not on a seat, not on a Chats row, not in a
    conversation header, not on a challenge card: those are places a person is
    named, and the intro is a place a person speaks.* Walked over the emitted
    contract, the way the sportsmanship words are, so a helpful field on a
    court person or a seat goes red rather than shipping.

    The second shape is the **author's own** profile read — where the line is
    read back to the person who wrote it so they can change or withdraw it
    (``docs/adr/0170`` §5, ``docs/adr/0179`` §6 and §8). Not a stranger's
    surface, and named here by name so a third shape still goes red. The search
    card that carried it went with the searches (#579)."""

    from app.api.contract import build_surface_spec
    from app.api.v1.player import player_api_router
    from tests.unit.test_no_response_carries_a_forbidden_fact import (
        schemas_reachable_from_responses,
    )

    schemas = schemas_reachable_from_responses(
        build_surface_spec("Raketa Player API", player_api_router)
    )
    assert schemas, "the walk found no schemas, so it would pass for ever"

    carrying = sorted(
        name
        for name, schema in schemas.items()
        if "intro" in (schema.get("properties") or {})
    )

    assert carrying == [
        "PlayerProfileReadResponse",
        "PlayerRecordResponse",
    ]


# ---------------------------------------------------------------------------
# The fold
# ---------------------------------------------------------------------------


def test_a_line_already_on_a_stream_is_not_re_checked() -> None:
    """The cap and the fence bind the write, never the replay."""

    recorded = Intro.recorded("x" * (INTRO_MAX_CHARACTERS + 40))

    assert len(recorded.text) == INTRO_MAX_CHARACTERS + 40


def test_a_blank_line_on_a_stream_is_a_broken_stream() -> None:
    """A blank leaves nothing behind, so a recorded blank is not a legitimate
    state — it is a precondition nothing on the write path can break."""

    with pytest.raises(InvariantViolated):
        Intro.recorded("   ")
