"""The intro: one line a player writes about themselves, fenced at the write.

**The first player-authored free text the platform shows to a stranger**
(``docs/adr/0170``). One line, at most ``INTRO_MAX_CHARACTERS`` after trimming,
no line breaks, in any language, one per player, and **optional** — a player who
skips has no intro, not an empty one, which is why ``written`` answers ``None``
for a blank rather than an ``Intro`` with nothing in it.

**The moderation story is a rule at the write, and the fence is contact.** The
realistic abuse of a line shown before any game exists is not rudeness — it is
*WhatsApp me on …*, which takes the arrangement, the reliability record and the
block out of the app. So what is refused is a phone-shaped run of digits, an
email, a URL or a bare domain, and an ``@handle``; nothing else is read. Rudeness
is what a block is for, and there is deliberately no sidecar: a classifier is a
dependency, a latency and a false-positive rate bought against an abuse nobody
has yet committed (§2). If one is ever needed it slots in here, where the rule
runs.

**The patterns are conservative in the ADR's sense — they err toward refusing.**
A false refusal costs a player a rewrite and the reason code says which kind;
a false admission leaks contact, and *a rule that lets a phone number through is
the worse failure*. The one place the two pull against each other is the digit
rule: *"Three sets, 100 zł to the winner"* must pass and *"600 123 456"* must
not, and the line between them is ``PHONE_DIGITS`` — the fewest digits a number
somebody could dial has. Every pattern is tuned from refusals, not from a guess,
and each is pinned by a line in ``tests/unit/test_intro.py``.

**Matched over a normalised copy, stored as typed.** The fence runs over the
NFKC form of the line — so full-width digits and a full-width ``＠`` are the
digits and the at-sign they are — while the text that is kept is the player's
own, trimmed and otherwise untouched. Nothing translates it, nothing lowercases
it, and it is never scored: the scorer's fence refuses the word
(``tests/unit/test_scorable_candidate_fence.py``).

**The write path refuses; the fold accepts.** ``written`` is what the commit
runs, and what the You tab's edit runs (``docs/adr/0179`` §6) — one fence for
both writes; ``recorded`` is what a replay runs and re-checks neither the cap
nor the fence, because the cap is a number product may move and a line already on a
stream was admitted when it was written. Lowering the cap must not un-rehydrate
every profile above the new one, which is the argument every value object in
this context makes.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Final

from app.kernel import invariant
from app.modules.player_profile.domain.errors import IntroNotAdmitted, IntroRefusal

#: The cap, in characters after trimming: **250** (``docs/adr/0200`` §9). It
#: was a hundred, to fit the deck card's two lines (``docs/adr/0170`` §4); that
#: card went with Classic play, and the record draws the line whole, in
#: quotation marks under the nickname, and never truncates it. Not served: both
#: sides hold it as a constant, the way the photo cap is held.
INTRO_MAX_CHARACTERS: Final = 250

#: The fewest digits a run has to hold before it reads as a number to dial.
#: Seven is the shortest local number in most numbering plans; a nine-digit
#: Polish mobile clears it and *100 zł* does not. A run is counted **across**
#: separators — spaces, dashes, dots, brackets, slashes, underscores, commas,
#: semicolons, a leading plus, any number of them — so spacing the digits out
#: is not a way past it. A score line with seven digits across it is refused
#: on the same rule, and that is the false positive the ADR's consequences
#: name; a pair of years is the one exemption, below.
PHONE_DIGITS: Final = 7

#: Top-level domains a bare domain is recognised by. A closed list on purpose:
#: matching *anything.anything* would refuse *e.g.* and *St.John*, and the cost
#: of the list is that a domain under a TLD not here crosses — which is a leak
#: of a kind the short-link and messaging domains below are the realistic
#: shape of. Extended from refusals, never guessed at. **And a bare domain is
#: read in lowercase only**: *"Moved here in May.In the evenings"* is a missing
#: space and not a site under ``.in``, and a domain somebody means to be typed
#: is typed the way it is typed. Two costs, one each way: ``Karolplays.PL``
#: crosses (unless a path follows it — ``Padel.Co/karol`` is caught), and a
#: lowercase run-on — *"may.in the evenings"* — is refused and costs a rewrite,
#: which is the side to err on. A URL with its scheme or ``www.`` is caught
#: whatever its case.
_TOP_LEVEL_DOMAINS: Final = (
    "com|net|org|info|biz|edu|gov|io|co|ai|app|dev|me|ly|gg|tv|xyz|site|online|"
    "link|chat|club|page|pro|eu|pl|de|uk|fr|es|it|nl|cz|sk|ua|lt|lv|ee|se|no|"
    "dk|fi|at|ch|be|pt|ie|ro|hu|ru|us|ca|au|br|in|jp|cn"
)

_EMAIL: Final = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
#: An at-sign followed by a name — a handle, or half an address (``karol@gmail``
#: has no dot for the email rule to find). ``@`` alone, or ``@`` before a
#: space, names nobody and is not one.
_HANDLE: Final = re.compile(r"@\w{2,}")
_URL: Final = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_BARE_DOMAIN: Final = re.compile(
    rf"(?<![\w.])(?:[\w-]+\.)+(?:{_TOP_LEVEL_DOMAINS})(?![\w.])",
    re.IGNORECASE,
)
#: A run of digits with any amount of separator between two of them — spaces,
#: dashes of every width, dots, brackets, slashes, underscores, commas,
#: semicolons — so ``600  123  456``, ``600, 123, 456``, ``600–123–456`` and
#: ``600_123_456`` are the run they are. A colon ends a run: *07:00-09:00* is
#: two times, not one number to dial.
_DIGIT_RUN: Final = re.compile(r"\+?\d(?:[\s().\-–—/_,;]*\d)+")
#: The one run of seven-plus digits that is not phone-shaped: two years with a
#: dash between them. *Played 2015-2022* is a career and not a number, and it
#: is the innocent line a digit rule refuses most often — so it is exempted by
#: shape, narrowly: exactly two four-digit groups that both read as years.
_YEAR_RANGE: Final = re.compile(r"^(?:19|20)\d{2}\s*[-–—/]\s*(?:19|20)\d{2}$")
#: Characters with no width, stripped before matching: a zero-width space
#: between every digit is invisible on a card and would split a run. NFKC does
#: not touch them, so they are removed by hand.
_ZERO_WIDTH: Final = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")


@dataclass(frozen=True, slots=True)
class Intro:
    """One player's own line, as a card and a record show it.

    Built through ``written`` or ``recorded`` and never directly, so that no
    caller holds an intro the fence never saw or a replay never recorded.
    """

    text: str

    def __post_init__(self) -> None:
        invariant(bool(self.text.strip()), "an intro with nothing in it")

    @classmethod
    def written(cls, text: str | None) -> Intro | None:
        """A line a player just wrote, or ``None`` where they wrote nothing.

        Trimmed first, so whitespace-only is treated as absent and the cap is
        counted on what will be kept. The shape is checked before the fence —
        a line the client should not have let through at all gets that reason
        rather than one about its content.
        """

        if text is None:
            return None
        line = text.strip()
        if not line:
            return None
        if len(line.splitlines()) > 1:
            raise IntroNotAdmitted(IntroRefusal.MULTILINE)
        if len(line) > INTRO_MAX_CHARACTERS:
            raise IntroNotAdmitted(IntroRefusal.TOO_LONG)
        if carries_contact(line):
            raise IntroNotAdmitted(IntroRefusal.CONTAINS_CONTACT)
        return cls(text=line)

    @classmethod
    def recorded(cls, text: str) -> Intro:
        """A line read back off a stream. **Not re-checked.**"""

        return cls(text=text)


def carries_contact(line: str) -> bool:
    """Does this line carry a way to reach somebody outside the app?

    The four shapes ``docs/adr/0170`` §2 names, and no fifth. Answered over the
    NFKC form so that a full-width digit or at-sign is the character it is.
    """

    folded = _ZERO_WIDTH.sub("", unicodedata.normalize("NFKC", line))
    if _EMAIL.search(folded) or _HANDLE.search(folded):
        return True
    if _URL.search(folded):
        return True
    if any(_is_a_domain(folded, domain) for domain in _BARE_DOMAIN.finditer(folded)):
        return True
    return any(_is_a_number_to_dial(run.group()) for run in _DIGIT_RUN.finditer(folded))


def _is_a_domain(folded: str, match: re.Match[str]) -> bool:
    """A bare domain is one typed in lowercase — or one with a path after it.

    ``May.In the evenings`` is a missing space; ``Padel.Co/karol`` is an address
    whatever its case, because nothing but a URL has a path.
    """

    domain = match.group()
    return domain == domain.lower() or folded[match.end() : match.end() + 1] == "/"


def _is_a_number_to_dial(run: str) -> bool:
    """Enough digits to dial, and not the one shape that is a pair of years."""

    if sum(character.isdigit() for character in run) < PHONE_DIGITS:
        return False
    return _YEAR_RANGE.match(run) is None


__all__ = ["INTRO_MAX_CHARACTERS", "PHONE_DIGITS", "Intro", "carries_contact"]
