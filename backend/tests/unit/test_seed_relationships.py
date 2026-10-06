"""The eleven relationship accounts: what they declare, and the ways a run
refuses them.

The relationships themselves went with the challenges (#578) and the accounts
stay, seated on the protagonist's played courts — so what is checked here is the
catalog: eleven accounts, each named for a pair from her side, each rated where
her courts are, and every refusal that fires before a session is opened.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.kernel import Sport
from app.seeds import relationships
from app.seeds.catalog import ACCOUNTS, PROTAGONISTS, RatedRun
from app.seeds.relationships import PROTAGONIST, RELATIONSHIP_ACCOUNTS

# ---------------------------------------------------------------------------
# 1. The declarations
# ---------------------------------------------------------------------------


def test_there_are_eleven_and_each_is_named_for_the_pair():
    """The catalog names an account for its **own state**; this file names one
    for a **relationship**, from the protagonist's side — and the description
    says what the account is now."""

    assert len(RELATIONSHIP_ACCOUNTS) == 11
    for account in RELATIONSHIP_ACCOUNTS:
        assert "you" in account.slug, account.slug
        assert account.description.startswith("Once "), account.slug


def test_only_one_protagonist_carries_relationships():
    """*You* is unambiguous only while it names one account."""

    assert PROTAGONIST in PROTAGONISTS
    slugs = {account.slug for account in RELATIONSHIP_ACCOUNTS}
    for other in PROTAGONISTS:
        assert other.slug not in slugs


def test_every_account_is_rated_in_padel_where_her_courts_are():
    for account in RELATIONSHIP_ACCOUNTS:
        rated = {
            scenario.sport
            for scenario in account.scenarios
            if isinstance(scenario, RatedRun)
        }
        assert Sport.PADEL in rated, account.slug


def test_each_is_dealt_its_own_level_rather_than_one_for_all():
    """Eleven people at one level are clones: on a court together they tie."""

    answers = {
        scenario.answers
        for account in RELATIONSHIP_ACCOUNTS
        for scenario in account.scenarios
        if isinstance(scenario, RatedRun) and scenario.sport is Sport.PADEL
    }

    assert len(answers) > 1


# ---------------------------------------------------------------------------
# 2. The refusals, at import
# ---------------------------------------------------------------------------


def test_an_account_with_no_padel_rating_is_refused(monkeypatch):
    """Whichever refusal reaches it first — the catalog's, about a declared
    intent with no rating behind it, or this layer's own."""

    first = RELATIONSHIP_ACCOUNTS[0]
    unrated = replace(
        first,
        scenarios=tuple(
            scenario
            for scenario in first.scenarios
            if not (isinstance(scenario, RatedRun) and scenario.sport is Sport.PADEL)
        ),
    )
    monkeypatch.setattr(
        relationships,
        "RELATIONSHIP_ACCOUNTS",
        (unrated,) + RELATIONSHIP_ACCOUNTS[1:],
    )

    with pytest.raises(RuntimeError, match=r"holds no (?i:padel) rating"):
        relationships._refuse_an_impossible_layer()


def test_two_accounts_at_one_slug_are_refused(monkeypatch):
    monkeypatch.setattr(
        relationships,
        "RELATIONSHIP_ACCOUNTS",
        RELATIONSHIP_ACCOUNTS + (RELATIONSHIP_ACCOUNTS[0],),
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

    stolen = replace(RELATIONSHIP_ACCOUNTS[0], slug=ACCOUNTS[0].slug)
    monkeypatch.setattr(
        relationships,
        "RELATIONSHIP_ACCOUNTS",
        (stolen,) + RELATIONSHIP_ACCOUNTS[1:],
    )

    with pytest.raises(RuntimeError, match=f"named '{ACCOUNTS[0].slug}'"):
        relationships._refuse_an_impossible_layer()


def test_the_protagonist_cannot_be_one_of_her_own_relationships(monkeypatch):
    monkeypatch.setattr(
        relationships,
        "RELATIONSHIP_ACCOUNTS",
        RELATIONSHIP_ACCOUNTS + (PROTAGONIST,),
    )

    with pytest.raises(RuntimeError):
        relationships._refuse_an_impossible_layer()
