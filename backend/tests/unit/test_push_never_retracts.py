"""Four rules about the push path, walked over its source.

Each one is a claim no behavioural test can make, because each is about code
that is **absent**: an operation nobody wrote, a branch nobody took, an import
nobody made, a second channel nobody declared. A suite can only assert what
happens, and every rule here is about what must never start happening.

They are cheap to hold and expensive to discover: the first three are decisions
ADR-0062 and ADR-0065 spend whole sections on, and each of them looks like an
improvement to somebody who has not read them.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.modules.now.domain.push import ANDROID_CHANNEL, ANDROID_IMPORTANCE

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app"
NOW = APP / "modules" / "now"

#: Every file in the push path, **named** rather than globbed into existence. A
#: glob that stops matching is reported green, which is the failure mode this
#: file exists to refuse in the code it walks.
WALKED = (
    NOW / "domain" / "push.py",
    NOW / "application" / "push.py",
    NOW / "infrastructure" / "push_stores.py",
    NOW / "infrastructure" / "push_sender.py",
    NOW / "infrastructure" / "sqlalchemy_push_models.py",
    NOW / "presentation" / "push_routes.py",
    NOW / "presentation" / "push_schemas.py",
)


def _tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_the_walk_reaches_every_file_in_the_push_path() -> None:
    """The membership above, against the tree, in both directions."""

    globbed = {
        path
        for path in NOW.rglob("*push*.py")
        if path.name != "__init__.py"
    }
    assert globbed == set(WALKED)
    for path in WALKED:
        assert path.exists(), path


# ---------------------------------------------------------------------------
# 1. Nothing is ever taken off a lock screen
# ---------------------------------------------------------------------------


def _sender_methods() -> list[str]:
    tree = _tree(NOW / "domain" / "ports.py")
    (protocol,) = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "PushSender"
    ]
    return [
        node.name
        for node in protocol.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def test_the_transport_can_only_send() -> None:
    """*Nothing is ever removed from a lock screen* as a port shape (ADR-0062).

    No platform offers server-side removal of a delivered alert as a guarantee:
    Apple documents replacement and documents removal nowhere, and Android's
    cancel needs the app to post the message itself — which kills the offer on
    force-quit and puts the sender on a seven-day deprioritisation window. So
    the retraction is carried by past-tense **wording**, and a port with a
    second method is the first place somebody would try to build one anyway.
    """

    assert _sender_methods() == ["send"]


def _identifiers(path: Path) -> set[str]:
    """Every name this module writes: functions, classes, attributes, variables.

    Names and never prose, which is the difference between a rule and a style
    guide: these files *explain* why nothing is withdrawn, at length, and a
    text search would forbid the explanation along with the operation.
    """

    found: set[str] = set()
    for node in ast.walk(_tree(path)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.add(node.name)
        elif isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.arg):
            found.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            found.add(node.arg)
    return found


@pytest.mark.parametrize(
    "word",
    ["cancel", "withdraw", "retract", "dismiss", "unsend", "revoke", "clear"],
)
def test_nothing_in_the_push_path_is_named_for_a_retraction(word: str) -> None:
    """The vocabulary, banned where it would be written.

    A *silent push that wakes the app to clear a notification* is the one
    mechanism that removes anything, and Apple attaches to it *"the system
    doesn't guarantee their delivery"*, a two-or-three-per-hour ceiling, death
    on force-quit, and the line that decides it: **"These limits are disabled
    when testing your app from Xcode"** — so it passes every check we could run
    and fails on the player's phone.

    The one deletion in this path is a **device row** whose token has moved to
    another account, which is about a phone rather than about a message and is
    named `register`.
    """

    for path in WALKED:
        offending = {name for name in _identifiers(path) if word in name.lower()}
        assert not offending, f"{path.name}: {sorted(offending)}"


def test_the_retraction_detector_can_tell_a_name_from_a_paragraph() -> None:
    """The negative control: the same word, as prose and as an operation.

    Every file walked above explains at length why nothing is ever withdrawn,
    so a detector that read the prose would forbid the reasoning and be deleted
    the first time somebody documented the rule.
    """

    explained = ROOT / "tests" / "unit" / "test_push_never_retracts.py"
    assert "withdraw" in explained.read_text(encoding="utf-8").lower()
    assert not {
        name for name in _identifiers(explained) if "withdraw" in name.lower()
    }


def test_the_only_deletion_is_a_token_that_moved_to_another_player() -> None:
    """Stated where it can fail, because it is the exception to the rule above.

    A phone signed into a second account still answers to the same token, and a
    row left behind would put one player's seats on somebody else's lock screen
    — which is the one failure in this channel worse than silence, and unfixable
    afterwards for exactly the reason nothing can be retracted.
    """

    deletions = [
        node
        for path in WALKED
        for node in ast.walk(_tree(path))
        if isinstance(node, ast.Call)
        and (getattr(node.func, "id", None) or getattr(node.func, "attr", None))
        == "delete"
    ]
    assert len(deletions) == 1

    (owner,) = [
        node
        for node in ast.walk(_tree(NOW / "infrastructure" / "push_stores.py"))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(inner, ast.Call)
            and (getattr(inner.func, "id", None) or getattr(inner.func, "attr", None))
            == "delete"
            for inner in ast.walk(node)
        )
    ]
    assert owner.name == "register"


# ---------------------------------------------------------------------------
# 2. Nothing branches on `timeSensitiveSetting`
# ---------------------------------------------------------------------------


def _branches_on_the_setting(tree: ast.AST) -> list[str]:
    """Every test, comparison or guard whose subtree reads the setting.

    Keyed on the *decision* nodes rather than on the identifier, because the
    field is read all over — a column mapped, a value stored, a type annotated —
    and none of that is a branch. What ADR-0065 forbids is the product behaving
    differently because of it.
    """

    def reads_it(node: ast.AST) -> bool:
        return any(
            (isinstance(inner, ast.Attribute) and inner.attr == "time_sensitive")
            or (isinstance(inner, ast.Name) and inner.id == "TimeSensitiveSetting")
            for inner in ast.walk(node)
        )

    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.While)) and reads_it(node.test):
            found.append(ast.dump(node.test)[:60])
        elif isinstance(node, ast.Compare) and reads_it(node):
            found.append(ast.dump(node)[:60])
        elif isinstance(node, ast.Match) and reads_it(node.subject):
            found.append(ast.dump(node.subject)[:60])
    return found


def test_nothing_anywhere_in_the_app_branches_on_the_setting() -> None:
    """ADR-0065: *revocation is reported, and nothing branches on it.*

    The cascade does not demote a player who has revoked Time Sensitive — she
    keeps her standby priority, still gets the seat, and still sees the line when
    she next looks. Demoting her would quietly cost her seats as a punishment for
    a settings choice, which is a worse outcome than the one it prevents.

    Walked over the **whole app** rather than over the push path, because the
    tempting place to write it is the cascade's pool, which is nowhere near
    these files.
    """

    offenders = [
        f"{path.relative_to(ROOT)}: {found}"
        for path in sorted(APP.rglob("*.py"))
        for found in _branches_on_the_setting(_tree(path))
    ]
    assert offenders == [], offenders


def test_the_branch_detector_can_tell_a_read_from_a_decision() -> None:
    """The negative control, driven both ways.

    A guard that has never been seen to fire is one nobody should watch, and a
    detector keyed on the identifier alone would fire on the column mapping and
    would have to be deleted the first time somebody stored the value.
    """

    branching = ast.parse(
        "if device.time_sensitive is TimeSensitiveSetting.DISABLED:\n    pass\n"
    )
    comparing = ast.parse("quiet = device.time_sensitive == 'disabled'\n")
    reading = ast.parse(
        "value = device.time_sensitive.value\n"
        "row.time_sensitive = device.time_sensitive.value\n"
        "setting = TimeSensitiveSetting(row.time_sensitive)\n"
    )

    assert _branches_on_the_setting(branching)
    assert _branches_on_the_setting(comparing)
    assert _branches_on_the_setting(reading) == []


# ---------------------------------------------------------------------------
# 3. One Android channel, and no Do Not Disturb bypass
# ---------------------------------------------------------------------------


def test_there_is_exactly_one_android_channel() -> None:
    """**Not two** (ADR-0065).

    *Seats you asked for* and *seats we found you* as separate channels reads as
    a kindness and is a mute switch on rungs 3–7 — the players likeliest to throw
    it, and the ones the open call depends on — with no server-side signal that
    it happened. One channel means muting standby costs a player the seats she
    actually wants, which is the honest price of the switch.
    """

    declared = {
        target.id
        for node in ast.walk(_tree(NOW / "domain" / "push.py"))
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name) and target.id.endswith("_CHANNEL")
    }
    assert declared == {"ANDROID_CHANNEL"}
    assert ANDROID_CHANNEL and ANDROID_IMPORTANCE == "high"


@pytest.mark.parametrize("word", ["bypassdnd", "bypass_dnd", "policy access"])
def test_notification_policy_access_is_never_asked_for(word: str) -> None:
    """A second permission prompt, to win one seat, on a phone that must already
    grant `POST_NOTIFICATIONS` and cannot be asked twice.

    ADR-0065 declines it: the ask costs more of the pool than the seats it wins,
    and `Raketa02/Raketa#36` found the call is worse than useless without the
    permission — Android's own service code silently overwrites the value, so
    nothing throws and the channel simply does not bypass.
    """

    for path in WALKED:
        assert word not in path.read_text(encoding="utf-8").lower(), path.name


# ---------------------------------------------------------------------------
# 4. The sentence cannot reach a venue
# ---------------------------------------------------------------------------


def test_the_module_that_writes_the_sentence_cannot_name_a_place() -> None:
    """*Sport, time and travel time; never the venue* (ADR-0062), as an import.

    A glance at somebody's lock screen must not publish where they will be. The
    composer is handed a `NamedSeat`, which carries a zone and no club — and the
    module cannot reach for one either, because the vocabulary that holds a club
    name is not imported into it. The seam where a club is actually dropped has
    its own case in `test_send_the_line.py`; this is the half that stops
    somebody adding it back.
    """

    imported = {
        name.name
        for node in ast.walk(_tree(NOW / "domain" / "push.py"))
        if isinstance(node, ast.ImportFrom)
        for name in node.names
    }
    for forbidden in ("Place", "Club", "ClubSnapshot", "Money"):
        assert forbidden not in imported, forbidden
