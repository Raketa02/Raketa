"""The ruleset's last two checks, where the engine and the contract both exist.

Most of what makes a ruleset believable is checked inside the engine, at import,
by ``validate_ruleset``. Two checks cannot live there, and it is the fence that
says so rather than a preference: **an engine may not import a module and may not
import pydantic**, so a tag id is a bare string to it and the wire union is
invisible.

So they run here, in the composition root — the one place that may see the
engine, the platform's vocabularies and the API contract at once.

1. **Every tag id a matrix row or the familiarity map names is a tag this
   platform actually serves.** A typo'd id is a row that can never fire, and a
   relationship that silently never fires is indistinguishable from one product
   decided against.
2. **The familiarity reading map is exhaustive over ``WHY_YOU_ARE_HERE``.** An id
   missing from it would fall to the default lean and read as *this player has no
   preference about repetition*, which is a claim about them rather than a gap in
   a table.
3. **Every evidence kind the ruleset can emit is present in the wire union**
   (``docs/adr/0106``). Two serialisations of one set of facts exist on purpose —
   storage stays open where the wire is closed — and this is the one check that
   stands between them. It is a **load failure rather than a lint** because the
   drift it catches is silent for exactly as long as nobody releases a ruleset
   with a new kind.

**Called at startup, so a malformed ruleset fails the deploy** and the previous
one keeps serving on the pods that are still up (``docs/adr/0119`` §6). With an
embedded ruleset there is no hot reload to fall back through, and there is
deliberately no fallback to defaults: a matcher that silently falls back is one
that quietly A/B tests against itself.

**Nothing here reads the environment.** A weight is not a setting — it is the
product's opinion about who a player should meet, which is behaviour a domain
test can observe (``docs/adr/0028``).
"""

from __future__ import annotations

from app.engines.matchfit.ruleset import Ruleset
from app.kernel import invariant
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.matchmaking.presentation.evidence import WIRE_EVIDENCE_KINDS
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_VOCABULARY,
    SocialTag,
    SocialTagGroup,
)


def verify_ruleset(ruleset: Ruleset = LIVE_RULESET) -> Ruleset:
    """Refuse a ruleset the platform's own vocabularies do not agree with.

    Raises ``InvariantViolated``. Defaulted to the live ruleset so the startup
    call reads as what it is, and parameterised so a test can drive a
    deliberately broken one through it — a guardrail that silently stops matching
    is worse than none, because you stop watching for it.
    """

    _verify_tag_ids(ruleset)
    _verify_familiarity_map(ruleset)
    _verify_evidence_kinds(ruleset)
    return ruleset


def _verify_tag_ids(ruleset: Ruleset) -> None:
    served = {tag.value for tag in SocialTag}
    named = {
        tag for row in ruleset.tags.relationship_matrix for tag in (row.a, row.b)
    } | set(ruleset.tags.familiarity_reading_map)
    unknown = sorted(named - served)
    invariant(
        not unknown,
        f"a ruleset names tag ids this platform does not serve: {unknown}",
    )


def _verify_familiarity_map(ruleset: Ruleset) -> None:
    """The map is exhaustive over the group it reads, and reads no other.

    Both directions matter. A missing id falls to the default lean and reads as a
    player with no preference; an id from another group would be familiarity
    reading a tag about the hour on court, which is not what *why you are here*
    means.
    """

    expected = {
        tag.value for tag in SOCIAL_TAG_VOCABULARY[SocialTagGroup.WHY_YOU_ARE_HERE]
    }
    read = set(ruleset.tags.familiarity_reading_map)
    invariant(
        read == expected,
        f"the familiarity reading map is not exhaustive over "
        f"{SocialTagGroup.WHY_YOU_ARE_HERE.value}: missing "
        f"{sorted(expected - read)}, unexpected {sorted(read - expected)}",
    )


def _verify_evidence_kinds(ruleset: Ruleset) -> None:
    unpublished = sorted(
        kind.value for kind in ruleset.emittable_evidence_kinds() - WIRE_EVIDENCE_KINDS
    )
    invariant(
        not unpublished,
        f"a ruleset can emit evidence kinds the wire union does not publish: "
        f"{unpublished} — the client generates a renderer per variant and would "
        f"draw nothing at all",
    )
