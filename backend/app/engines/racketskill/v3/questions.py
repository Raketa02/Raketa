"""Version 3's question bank — every question, for every sport.

Each answer carries the evidence it encodes to: a ``(μ, σ)`` pair *before* the
irreducible self-report bias is folded in by the engine, in quadrature, on every
answer alike. That symmetry is what makes under-reporting no more profitable than
over-reporting, and what makes the value of each extra question decay to zero on
its own.

The bank is organised by evidence category — recent activity (regularity,
volume), competitive context (environment, relative performance), match
execution (three difficulty tiers) and tactical execution (two questions). Two
questions widen uncertainty rather than moving the estimate: **layoff** (σ only,
never μ) is a recent-activity question asked only of a player with a history.

Every question is a short situation clause plus a short question clause,
**situation first**, because a player who has to hold several clauses in their
head before answering will answer carelessly, and a careless answer is
indistinguishable from an honest one by the time it reaches the arithmetic.

Padel and badminton are worded for **doubles** (partner, pair); tennis and squash
for **singles** — derived from the registry's player count, never hardcoded. Basic
execution questions carry no sport-specific jargon: they are the same easy rally
in every sport.

Every constant here is a hypothesis, to be falsified against the ratings it
generates. Only the opening "I have never played" anchor is verified by hand
against the published beginner result.
"""

from __future__ import annotations

from app.engines.assessment import AnswerOption, Question
from app.kernel import SPORT_SPECS, Sport

# --- Question identities -------------------------------------------------------

OPENING_QUESTION_ID = "opening.regularity"
VOLUME_QUESTION_ID = "recent.volume"
LAYOFF_QUESTION_ID = "history.layoff"
ENVIRONMENT_QUESTION_ID = "context.environment"
RELATIVE_QUESTION_ID = "context.relative"

# The difficulty tiers, in vocabulary shared by the wire, the engine and the
# screen. There is exactly one execution question per tier per sport.
TIER_BASIC = "basic"
TIER_STANDARD = "standard"
TIER_DISCRIMINATING = "discriminating"
TIERS: tuple[str, ...] = (TIER_BASIC, TIER_STANDARD, TIER_DISCRIMINATING)

EXECUTION_QUESTION_IDS: dict[str, str] = {
    TIER_BASIC: "execution.basic",
    TIER_STANDARD: "execution.standard",
    TIER_DISCRIMINATING: "execution.discriminating",
}
TACTICAL_QUESTION_IDS: tuple[str, ...] = ("tactical.reading", "tactical.decision")

# --- Categories (the screen title, read last on a top-down screen) -------------

CATEGORY_REGULARITY = "Playing regularly"
CATEGORY_VOLUME = "Recent matches"
CATEGORY_LAYOFF = "Time away"
CATEGORY_ENVIRONMENT = "Who you play"
CATEGORY_RELATIVE = "How those matches go"
CATEGORY_EXECUTION = "On court"
CATEGORY_TACTICAL = "Reading the game"

_QUALIFIER = "Choose the option that fits best."

# --- Recent activity: regularity (the opening question) ------------------------

NEVER_PLAYED_OPTION_ID = "never-played"

# option id -> (μ, σ) evidence, before the self-report bias is combined in.
_REGULARITY_EVIDENCE: dict[str, tuple[float, float]] = {
    NEVER_PLAYED_OPTION_ID: (1.20, 0.75),
    "tried-a-few-times": (1.80, 0.90),
    "occasional": (2.60, 0.90),
    "regular": (3.30, 0.85),
    "frequent": (3.90, 0.85),
}

# The one genuinely ambiguous regularity answer — "now and then" spans anything
# from monthly to twice a week — so volume is asked only after this one.
AMBIGUOUS_REGULARITY_OPTIONS = frozenset({"occasional"})

# A player "has a history" if they play, or used to play, meaningfully. Somebody
# who has only tried a few times has no break to describe, so is never asked about
# a layoff; a never-played beginner never reaches this question at all.
HISTORY_REGULARITY_OPTIONS = frozenset({"occasional", "regular", "frequent"})

# --- Recent activity: match volume ---------------------------------------------

LOW_VOLUME_OPTION_ID = "v0"

_VOLUME_EVIDENCE: dict[str, tuple[float, float]] = {
    LOW_VOLUME_OPTION_ID: (1.90, 0.90),
    "v1": (2.40, 0.90),
    "v2": (3.00, 0.85),
    "v3": (3.50, 0.85),
}

_VOLUME_OPTIONS: tuple[tuple[str, str], ...] = (
    (LOW_VOLUME_OPTION_ID, "I haven't played a match in months"),
    ("v1", "A handful over the last few months"),
    ("v2", "A few most months"),
    ("v3", "At least one most weeks"),
)

# --- Recent activity: layoff (σ only, never μ) ---------------------------------

# option id -> the σ (in level units) a layoff adds in quadrature. A player who
# was good two years ago has no obligation to still be, and none to have got
# worse; the honest move is to widen uncertainty, not to lower the level.
_LAYOFF_SIGMA: dict[str, float] = {
    "l0": 0.00,
    "l1": 0.25,
    "l2": 0.50,
    "l3": 0.80,
}

_LAYOFF_OPTIONS: tuple[tuple[str, str], ...] = (
    ("l0", "I'm still playing regularly"),
    ("l1", "Within the last year"),
    ("l2", "One to two years ago"),
    ("l3", "More than two years ago"),
)

# --- Competitive context: environment + relative performance -------------------

_ENVIRONMENT_EVIDENCE: dict[str, tuple[float, float]] = {
    "env0": (2.20, 0.90),
    "env1": (2.80, 0.85),
    "env2": (3.40, 0.85),
    "env3": (4.00, 0.85),
}

_ENVIRONMENT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("env0", "Casual, social games with friends"),
    ("env1", "Friendly club games and social matches"),
    ("env2", "Organised club matches or a local league"),
    ("env3", "Competitive leagues or tournaments"),
)

# Relative performance is an *offset on the environment answer*, never a level of
# its own: winning most of your matches means something completely different in
# two different clubs. The combined competitive-context evidence carries the
# widest band in the bank.
_RELATIVE_OFFSET: dict[str, float] = {
    "r0": -0.40,
    "r1": 0.00,
    "r2": 0.40,
    "r3": 0.60,
}
RELATIVE_SIGMA = 1.10  # the widest band in the bank

_RELATIVE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("r0", "I usually come off worse"),
    ("r1", "We're pretty evenly matched"),
    ("r2", "I usually come out ahead"),
    ("r3", "I win almost every time"),
)

# --- Execution: three tiers, five shared options -------------------------------

# The same five options on every execution question, so a player never has to
# relearn the scale. Their numeric meaning depends entirely on the tier the
# question was asked at — which is chosen from the running estimate.
EXECUTION_OPTIONS: tuple[tuple[str, str], ...] = (
    ("e0", "Not really — not yet"),
    ("e1", "Only now and then"),
    ("e2", "About half the time"),
    ("e3", "Most of the time"),
    ("e4", "Almost always, even under pressure"),
)

_EXECUTION_BASE: dict[str, float] = {
    TIER_BASIC: 1.50,
    TIER_STANDARD: 2.40,
    TIER_DISCRIMINATING: 3.30,
}
_EXECUTION_STEP = 0.35
_EXECUTION_SIGMA: dict[str, float] = {
    TIER_BASIC: 0.75,
    TIER_STANDARD: 0.65,
    TIER_DISCRIMINATING: 0.55,
}

# Basic execution is the same jargon-free warm-up rally in every sport — only the
# framing changes between doubles and singles.
_BASIC_DOUBLES = (
    "You and your partner are having a gentle warm-up.",
    "Can you keep an easy rally going back and forth?",
)
_BASIC_SINGLES = (
    "You're having a gentle warm-up with someone.",
    "Can you keep an easy rally going back and forth?",
)

# Standard and discriminating carry each sport's own vocabulary. (situation, text)
_EXECUTION_COPY: dict[Sport, dict[str, tuple[str, str]]] = {
    Sport.PADEL: {
        TIER_STANDARD: (
            "A rally has settled into a steady exchange down the middle.",
            "Can you and your partner control the ball off the back glass?",
        ),
        TIER_DISCRIMINATING: (
            "The other pair lifts a deep lob over your heads.",
            "Can you play it off the back wall and retake the net?",
        ),
    },
    Sport.TENNIS: {
        TIER_STANDARD: (
            "A baseline rally has settled into a steady rhythm.",
            "Can you rally with depth and direction off both wings?",
        ),
        TIER_DISCRIMINATING: (
            "Your opponent pulls you wide with a heavy angled ball.",
            "Can you defend, recover, and reset the point on the run?",
        ),
    },
    Sport.SQUASH: {
        TIER_STANDARD: (
            "A rally has settled into a length game on one side.",
            "Can you hit a consistent length that pushes your opponent back?",
        ),
        TIER_DISCRIMINATING: (
            "Your opponent plays a tight ball into the back corner.",
            "Can you dig it out and counter with a good length?",
        ),
    },
    Sport.BADMINTON: {
        TIER_STANDARD: (
            "Your pair has settled into an attacking front-and-back shape.",
            "Can you and your partner keep the shuttle down and attack?",
        ),
        TIER_DISCRIMINATING: (
            "The opponents lift the shuttle deep to your backhand corner.",
            "Can you smash or clear under pressure and hold your side?",
        ),
    },
}

# --- Tactical: two questions per sport ------------------------------------------

TACTICAL_OPTIONS: tuple[tuple[str, str], ...] = (
    ("t0", "I mostly just react in the moment"),
    ("t1", "Sometimes, when I have time to think"),
    ("t2", "Usually — I read most situations"),
    ("t3", "Almost always, it's second nature"),
)

_TACTICAL_BASE = 2.20
_TACTICAL_STEP = 0.55
_TACTICAL_SIGMA = 0.80

_TACTICAL_COPY: dict[Sport, tuple[tuple[str, str], tuple[str, str]]] = {
    Sport.PADEL: (
        (
            "Your pair is pinned deep and under real pressure.",
            "Do you know when to lob to reset the point?",
        ),
        (
            "During a point a gap opens on the far side.",
            "Can you pick the right moment to attack it?",
        ),
    ),
    Sport.TENNIS: (
        (
            "You're in a neutral baseline rally with no advantage.",
            "Do you know when to change direction and when to wait?",
        ),
        (
            "You've pulled your opponent well out of position.",
            "Can you choose the shot that finishes the point?",
        ),
    ),
    Sport.SQUASH: (
        (
            "You've worked your opponent to the back of the court.",
            "Do you know when to play it short to the front?",
        ),
        (
            "You're both battling for the T in a fast rally.",
            "Can you read where the next ball is going early?",
        ),
    ),
    Sport.BADMINTON: (
        (
            "Your pair is defending a long, sustained attack.",
            "Do you know when to lift and when to drive flat?",
        ),
        (
            "A weak return floats up loose near the net.",
            "Can you read it early and move in to finish?",
        ),
    ),
}

# A plain noun for each sport, so the copy reads naturally. The registry enum is
# uppercase; the questionnaire speaks to a person.
_SPORT_NOUN: dict[Sport, str] = {
    Sport.PADEL: "padel",
    Sport.TENNIS: "tennis",
    Sport.SQUASH: "squash",
    Sport.BADMINTON: "badminton",
}


def _is_doubles(sport: Sport) -> bool:
    """Whether the sport is played as doubles — derived, never hardcoded."""

    return SPORT_SPECS[sport].players == 4


def _options(pairs: tuple[tuple[str, str], ...]) -> tuple[AnswerOption, ...]:
    return tuple(AnswerOption(option_id, text) for option_id, text in pairs)


# --- Question builders ---------------------------------------------------------


def opening_question(sport: Sport) -> Question:
    """The regularity question that opens every assessment, situation first."""

    noun = _SPORT_NOUN[sport]
    return Question(
        id=OPENING_QUESTION_ID,
        category=CATEGORY_REGULARITY,
        situation=f"To start, think about how {noun} fits into your life these days.",
        text=f"How often do you play {noun}?",
        qualifier=_QUALIFIER,
        tier=None,
        options=(
            AnswerOption(NEVER_PLAYED_OPTION_ID, "I have never played"),
            AnswerOption("tried-a-few-times", "I've played a handful of times"),
            AnswerOption("occasional", "I play now and then"),
            AnswerOption("regular", "I play most weeks"),
            AnswerOption("frequent", "I play several times a week"),
        ),
    )


def volume_question(sport: Sport) -> Question:
    """How many real matches lately — disambiguates an ambiguous regularity."""

    return Question(
        id=VOLUME_QUESTION_ID,
        category=CATEGORY_VOLUME,
        situation="Think about the actual matches or games you've played recently.",
        text="How many real matches have you played lately?",
        qualifier=_QUALIFIER,
        tier=None,
        options=_options(_VOLUME_OPTIONS),
    )


def layoff_question(sport: Sport) -> Question:
    """When the player last played regularly — widens σ, never touches μ."""

    return Question(
        id=LAYOFF_QUESTION_ID,
        category=CATEGORY_LAYOFF,
        situation="It sounds like it may have been a while since you played much.",
        text="When did you last play regularly?",
        qualifier=_QUALIFIER,
        tier=None,
        options=_options(_LAYOFF_OPTIONS),
    )


def environment_question(sport: Sport) -> Question:
    """The competitive context, asked before any execution question."""

    noun = _SPORT_NOUN[sport]
    return Question(
        id=ENVIRONMENT_QUESTION_ID,
        category=CATEGORY_ENVIRONMENT,
        situation=f"Think about the kind of {noun} you usually play.",
        text="What best describes your matches?",
        qualifier=_QUALIFIER,
        tier=None,
        options=_options(_ENVIRONMENT_OPTIONS),
    )


def relative_question(sport: Sport) -> Question:
    """Relative performance — read as an offset on the environment answer."""

    return Question(
        id=RELATIVE_QUESTION_ID,
        category=CATEGORY_RELATIVE,
        situation="Now think about the people you usually play against.",
        text="How do those matches usually go for you?",
        qualifier=_QUALIFIER,
        tier=None,
        options=_options(_RELATIVE_OPTIONS),
    )


def execution_question(sport: Sport, tier: str) -> Question:
    """One execution question at a given difficulty tier."""

    if tier == TIER_BASIC:
        situation, text = _BASIC_DOUBLES if _is_doubles(sport) else _BASIC_SINGLES
    else:
        situation, text = _EXECUTION_COPY[sport][tier]
    return Question(
        id=EXECUTION_QUESTION_IDS[tier],
        category=CATEGORY_EXECUTION,
        situation=situation,
        text=text,
        qualifier=_QUALIFIER,
        tier=tier,
        options=_options(EXECUTION_OPTIONS),
    )


def tactical_question(sport: Sport, index: int) -> Question:
    """One of the two tactical questions for a sport."""

    situation, text = _TACTICAL_COPY[sport][index]
    return Question(
        id=TACTICAL_QUESTION_IDS[index],
        category=CATEGORY_TACTICAL,
        situation=situation,
        text=text,
        qualifier=_QUALIFIER,
        tier=None,
        options=_options(TACTICAL_OPTIONS),
    )


def all_questions_for(sport: Sport) -> tuple[Question, ...]:
    """Every question the bank can ask for a sport — for introspection and tests."""

    return (
        opening_question(sport),
        volume_question(sport),
        layoff_question(sport),
        environment_question(sport),
        relative_question(sport),
        *(execution_question(sport, tier) for tier in TIERS),
        *(
            tactical_question(sport, index)
            for index in range(len(TACTICAL_QUESTION_IDS))
        ),
    )


# --- Evidence lookups (consumed by the engine's fusion) ------------------------


def regularity_evidence(option_id: str) -> tuple[float, float] | None:
    return _REGULARITY_EVIDENCE.get(option_id)


def volume_evidence(option_id: str) -> tuple[float, float] | None:
    return _VOLUME_EVIDENCE.get(option_id)


def environment_evidence(option_id: str) -> tuple[float, float] | None:
    return _ENVIRONMENT_EVIDENCE.get(option_id)


def relative_offset(option_id: str) -> float | None:
    return _RELATIVE_OFFSET.get(option_id)


def layoff_sigma(option_id: str) -> float | None:
    return _LAYOFF_SIGMA.get(option_id)


def execution_evidence(tier: str, option_id: str) -> tuple[float, float] | None:
    index = _option_index(EXECUTION_OPTIONS, option_id)
    if index is None or tier not in _EXECUTION_BASE:
        return None
    mu = _EXECUTION_BASE[tier] + index * _EXECUTION_STEP
    return mu, _EXECUTION_SIGMA[tier]


def tactical_evidence(option_id: str) -> tuple[float, float] | None:
    index = _option_index(TACTICAL_OPTIONS, option_id)
    if index is None:
        return None
    return _TACTICAL_BASE + index * _TACTICAL_STEP, _TACTICAL_SIGMA


def tier_for_execution_id(question_id: str) -> str | None:
    for tier, qid in EXECUTION_QUESTION_IDS.items():
        if qid == question_id:
            return tier
    return None


def _option_index(pairs: tuple[tuple[str, str], ...], option_id: str) -> int | None:
    for index, (candidate, _text) in enumerate(pairs):
        if candidate == option_id:
            return index
    return None
