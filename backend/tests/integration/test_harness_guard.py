"""The harness's own gate: a pipeline cannot run these cases without a Postgres
and still report green.

Nothing here touches a database — these are assertions about the resolution
rules in `tests.integration.postgres`, so they run in the ordinary suite, on a
laptop with no Docker, on every `make check`. That is deliberate. The guard
exists to catch a workflow edit, and a guard that can only be checked by a
runner that already has the thing it is guarding is not a guard.

`tests/unit/test_sqlalchemy_event_store.py` is the shape being defended against
and is still in the tree: it skips unless `EVENT_TEST_DATABASE_URL` is set, and
that variable is set by the same file that would be edited to remove it. Its
Postgres case is reported as a finding on #62 rather than changed here.
"""

import pytest

from tests.integration.postgres import (
    URL_VARIABLES,
    is_postgres_url,
    resolve_url,
    running_in_ci,
    to_asyncpg_url,
)

PG = "postgresql://raketa_user:raketa_pwd@localhost:5432/raketa"
SQLITE = "sqlite+aiosqlite:///:memory:"


# --- the requirement is keyed on something the workflow does not own ----------


def test_ci_is_detected_from_the_runner_not_from_a_project_variable():
    """`CI` is set by GitHub Actions itself. If the requirement were keyed on
    `POSTGRES_TEST_URL`, deleting that line from the workflow would delete the
    requirement to have it — the failure mode this whole module exists for."""
    assert running_in_ci({"CI": "true"}) is True
    assert "CI" not in URL_VARIABLES


@pytest.mark.parametrize("value", ["true", "1", "yes", "TRUE", "on"])
def test_a_pipeline_is_recognised(value):
    assert running_in_ci({"CI": value}) is True


@pytest.mark.parametrize("environ", [{}, {"CI": ""}, {"CI": "0"}, {"CI": "false"}])
def test_a_laptop_is_not_a_pipeline(environ):
    """A developer who exported `CI=0` to quiet some other tool has not asked to
    be required to run Postgres."""
    assert running_in_ci(environ) is False


# --- what counts as a URL -----------------------------------------------------


def test_a_postgres_url_is_resolved_and_normalised_onto_the_async_driver():
    assert resolve_url({"POSTGRES_TEST_URL": PG}) == (
        "postgresql+asyncpg://raketa_user:raketa_pwd@localhost:5432/raketa"
    )


def test_an_already_async_url_is_left_alone():
    url = "postgresql+asyncpg://u:p@h:5432/d"
    assert resolve_url({"POSTGRES_TEST_URL": url}) == url


def test_the_explicit_variable_wins_over_the_applications_own():
    """So the integration suite can be pointed somewhere other than the writer
    database without moving the application's configuration."""
    resolved = resolve_url({"POSTGRES_TEST_URL": PG, "WRITER_DB_URL": "postgres://x/y"})
    assert resolved is not None and resolved.endswith("/raketa")


def test_ci_needs_no_second_variable_because_writer_db_url_is_already_postgres():
    """The backend CI job has set `WRITER_DB_URL` to its Postgres service since
    long before this suite existed."""
    assert resolve_url({"WRITER_DB_URL": PG}) is not None


@pytest.mark.parametrize(
    "environ",
    [
        {},
        {"POSTGRES_TEST_URL": ""},
        {"POSTGRES_TEST_URL": "   "},
        {"WRITER_DB_URL": SQLITE},
        {"POSTGRES_TEST_URL": SQLITE, "WRITER_DB_URL": SQLITE},
        {"POSTGRES_TEST_URL": "mysql://u:p@h/d"},
    ],
)
def test_no_postgres_url_resolves_to_none(environ):
    """A variable holding SQLite counts as *no URL*, not as one to try. The API
    suite's `WRITER_DB_URL` is SQLite, and connecting an interval-exclusion test
    to it fails with a syntax error that reads like a broken test."""
    assert resolve_url(environ) is None


def test_a_sqlite_url_is_never_mistaken_for_postgres():
    assert is_postgres_url(SQLITE) is False
    assert to_asyncpg_url(SQLITE) == SQLITE


@pytest.mark.parametrize(
    "url",
    [PG, "postgres://u:p@h/d", "postgresql+asyncpg://u:p@h/d"],
)
def test_every_spelling_of_a_postgres_url_is_accepted(url):
    assert is_postgres_url(url) is True
    assert to_asyncpg_url(url).startswith("postgresql+asyncpg://")


# --- the two halves compose into the rule the suite is built on ---------------


def test_a_pipeline_without_a_database_is_a_failure_not_a_skip():
    """The whole point, stated as one assertion.

    `postgres_url` calls `pytest.fail` on exactly this combination. Asserting the
    combination here rather than invoking the fixture keeps it checkable in the
    ordinary suite: a test that ran the fixture would have to skip on a laptop,
    which is the outcome under test.
    """
    assert running_in_ci({"CI": "true"}) is True
    assert resolve_url({"CI": "true", "WRITER_DB_URL": SQLITE}) is None


def test_a_laptop_without_a_database_is_a_skip_not_a_failure():
    assert running_in_ci({}) is False
    assert resolve_url({"WRITER_DB_URL": SQLITE}) is None
