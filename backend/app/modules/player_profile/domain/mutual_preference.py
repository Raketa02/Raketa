"""The mutual gender gate, as one predicate. **Three callers, one rule.**

``docs/adr/0096`` makes the gate mutual — a pairing is admissible only if each
side passes the other's preference — and the rule was written once, in
``matchmaking.domain.gates``, with a docstring saying why it must stay once:

    the same gate is evaluated in two places … and a second implementation of a
    mutual safety gate is exactly the thing that ends up satisfied in one place
    and not the other.

**The send makes three, and it cannot import the first.** The import arrow runs
``matchmaking -> challenges`` and never back (``.importlinter``), so a send
re-verifying this gate in its own transaction has no way to reach the matcher's
copy. Something had to move, and what moved is the **judgement**: it lives here,
beside the two enums it reads, where every context that holds a profile can call
it.

**The reading stayed with each caller**, and that is the whole of the split. The
docstring's fear is about the *rule*, not about the source: the matcher reads a
candidate off an index row whose fields are strings from a log that outlives this
deployment, and the send reads live profiles because a safety gate must never be
evaluated on a stale copy. Two readers, two failure modes, one verdict.

**This is not the gate moving into the vocabulary.** ``gender.py`` fences the
comparison out of itself so that the module ``app/engines/matchfit/`` imports
carries no matching rule; that fence is intact, because nothing here is imported
by the vocabulary and the engine still never sees a gender. What is here is a
predicate over two people's answers, in the context that owns the answers.
"""

from __future__ import annotations

from app.modules.player_profile.domain.gender import Gender, GenderPreference


def preferences_are_mutual(
    *,
    one_gender: Gender | None,
    one_preference: GenderPreference | None,
    other_gender: Gender | None,
    other_preference: GenderPreference | None,
) -> bool:
    """Whether these two may be shown to each other. **Closed, and told to nobody.**

    Both preferences have to be readable and both have to be satisfied. The
    asymmetry between the two facts is the rule rather than an accident:

    - **An unreadable preference excludes.** ``None`` here means the safety
      setting could not be evaluated — a profile that does not exist, a code from
      a vocabulary this build does not serve — and *a gate that cannot be
      evaluated excludes*. It is never read as ``ANY``: a guess would be
      satisfied by whoever happened to match it, which is the failure wearing the
      shape of a fix.
    - **An unreadable answer is an absence**, and an absence is only fatal to a
      preference that needed it. A pair who both ask for anybody never read a
      gender at all, which is why an unanswered question costs nothing until
      somebody's safety setting depends on it.

    It takes four scalars rather than two people, because the two sides arrive
    from different places in every caller — an index row against a live profile,
    or two live profiles — and a signature that accepted a *person* would be one
    a caller could pass the wrong kind of person to.
    """

    if one_preference is None or other_preference is None:
        return False
    return _satisfies(one_preference, other_gender) and _satisfies(
        other_preference, one_gender
    )


def _satisfies(preference: GenderPreference, gender: Gender | None) -> bool:
    """Whether one side's answer clears the other side's preference.

    ``PREFER_NOT_TO_SAY`` and *no answer at all* land in the same place here and
    are still different facts: neither satisfies a narrowed preference, and both
    satisfy ``ANY``. The difference between them lives on the profile, where it
    is a fact about whether the question was asked.
    """

    if preference is GenderPreference.ANY:
        return True
    if preference is GenderPreference.WOMEN_ONLY:
        return gender is Gender.WOMAN
    return gender is Gender.MAN
