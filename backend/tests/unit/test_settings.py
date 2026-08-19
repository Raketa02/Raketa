"""The settings object: the profile it derives, and the configuration it refuses.

The settings object is plain — no application, no database, no HTTP — which makes it
the highest available seam for almost everything in the four-environment change. Every
test here constructs it directly, so what is asserted holds for any construction path
and not only for a process that happens to serve requests.

Two disciplines are worth naming, because both are easy to get wrong:

**Isolation.** `Settings` reads the process environment and a `.env` file. `conftest.py`
sets `JWT_SECRET_KEY` and `WRITER_DB_URL` for the API suite, and either would silently
disarm a refusal here — a production settings object would inherit a non-default signing
key and never trip the refusal that this file claims to prove fires. So every case is
built through `build()`, which is handed an environment scrubbed of every setting name.

**Poison values.** Each refusal case carries a database URL with a password in it and a
recognisable secret. No refusal message may contain either. That is the acceptance
criterion *"no refusal message contains the offending value"* in the form that actually
matters: a refusal goes into a log aggregator or a crash report, and a `WRITER_DB_URL`
carries a credential.
"""

import logging

import pytest

from app.core.config import (
    DEFAULT_JWT_SECRET_KEY,
    ENVIRONMENT_PROFILES,
    UNPROVISIONED,
    ConfigurationError,
    Environment,
    Settings,
)
from app.core.logging import configure_logging

#: A password no legitimate message has any reason to contain.
POISON_PASSWORD = "hunter2-do-not-log-me"
POISON_DB_URL = f"postgresql+asyncpg://u:{POISON_PASSWORD}@db.example:5432/raketa"
POISON_SECRET = "s3cret-do-not-log-me"


@pytest.fixture
def clean_env(monkeypatch):
    """Scrub every setting name from the process environment.

    Without this, `conftest.py`'s module-level `os.environ.setdefault` calls leak into
    every case below — and they leak in the direction that makes a refusal *stop
    firing*, which is the direction a passing test cannot distinguish from a working
    guard.
    """
    for name in Settings.model_fields:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def build(**overrides) -> Settings:
    """Construct settings from nothing but the arguments given.

    `_env_file=None` because a developer with a real `backend/.env` on disk must not
    get different test results from CI.
    """
    return Settings(_env_file=None, **overrides)


def settings_for(env, **overrides) -> Settings:
    """A minimally *valid* configuration for `env`, plus whatever a case overrides.

    What each environment needs differs, which is the whole subject of this file: a
    laptop needs nothing, an unprovisioned environment needs a host and a database,
    and production needs the four things it refuses to start without.
    """
    env = Environment(env)
    base: dict = {"APP_ENV": env}
    if env in UNPROVISIONED:
        base |= {"APP_HOST": "10.0.0.1", "WRITER_DB_URL": POISON_DB_URL}
    if env is Environment.PRODUCTION:
        base |= {
            "JWT_SECRET_KEY": POISON_SECRET,
            "WRITER_DB_URL": POISON_DB_URL,
            "DB_SSL_MODE": "require",
            "ALLOW_ORIGINS": ["https://club.raketa.example"],
            "ALLOW_CREDENTIALS": True,
        }
    return build(**{**base, **overrides})


def production(**overrides) -> Settings:
    """A production configuration that is valid unless a case breaks it deliberately."""
    return settings_for(Environment.PRODUCTION, **overrides)


# --------------------------------------------------------------------------- #
# The vocabulary
# --------------------------------------------------------------------------- #


def test_the_four_names_and_no_others() -> None:
    """The whole point of the enum. A fifth spelling is a fifth deployment target."""
    assert [e.value for e in Environment] == [
        "local",
        "development",
        "staging",
        "production",
    ]


@pytest.mark.parametrize("name", ["local", "development", "staging", "production"])
def test_each_name_is_accepted(clean_env, name: str) -> None:
    assert settings_for(name).APP_ENV is Environment(name)


@pytest.mark.parametrize("name", ["dev", "prod", "prd", "test", "DEVELOPMENT", ""])
def test_an_unrecognised_environment_is_refused(clean_env, name: str) -> None:
    """`dev` and `prod` are in the list on purpose — they are the *old* spellings.

    They must fail rather than be quietly accepted as synonyms, because a synonym is
    how the two names drift back apart. `DEVELOPMENT` is there because a `StrEnum`
    lookup is case-sensitive and that is the intended reading: one spelling.

    That the message does not echo the rejected value is asserted in
    `test_no_refusal_echoes_a_value`, with a sentinel that is not a substring of any
    legal name — `dev` and `prod` are, so asserting it here would fail on the
    legitimate list of alternatives the message is obliged to offer.
    """
    with pytest.raises(ConfigurationError) as exc:
        build(APP_ENV=name)
    assert "APP_ENV" in str(exc.value)


def test_the_default_environment_is_local(clean_env) -> None:
    assert build().APP_ENV is Environment.LOCAL


# --------------------------------------------------------------------------- #
# The derived profile
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("env", list(Environment))
def test_each_environment_derives_its_documented_profile(clean_env, env) -> None:
    settings = settings_for(env)
    profile = ENVIRONMENT_PROFILES[env]
    assert settings.DEBUG is profile.DEBUG
    assert settings.LOG_LEVEL == profile.LOG_LEVEL
    assert settings.LOG_JSON is profile.LOG_JSON


def test_local_is_the_readable_one(clean_env) -> None:
    """Pinned separately from the table, so a retune of the table is a visible diff
    against a stated intent rather than a test that follows it wherever it goes."""
    settings = build(APP_ENV="local")
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.LOG_JSON is False


def test_everything_deployed_logs_json_and_is_not_debug(clean_env) -> None:
    for env in (Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION):
        profile = ENVIRONMENT_PROFILES[env]
        assert profile.LOG_JSON is True, env
        assert profile.DEBUG is False, env


@pytest.mark.parametrize(
    "field, override",
    # Each value is the opposite of what `local` derives, so a case that stopped
    # overriding anything would fail the first assertion rather than pass vacuously.
    [("DEBUG", False), ("LOG_LEVEL", "WARNING"), ("LOG_JSON", True)],
)
def test_an_explicit_override_beats_the_derived_default(
    clean_env, field: str, override
) -> None:
    """The escape hatch that keeps the mechanism usable: verbose logging in staging
    while chasing a bug must not require abandoning the derived profile."""
    assert getattr(ENVIRONMENT_PROFILES[Environment.LOCAL], field) != override
    settings = build(APP_ENV="local", **{field: override})
    assert getattr(settings, field) == override


def test_an_override_from_the_process_environment_also_wins(clean_env) -> None:
    """`model_fields_set` is what distinguishes "set" from "defaulted", and a value
    arriving as an env var has to count — that is how it will actually be set."""
    clean_env.setenv("LOG_LEVEL", "ERROR")
    assert build(APP_ENV="local").LOG_LEVEL == "ERROR"


# --------------------------------------------------------------------------- #
# The refusals
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("env", ["development", "staging"])
def test_an_unprovisioned_environment_without_a_host_refuses(clean_env, env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        build(APP_ENV=env, WRITER_DB_URL=POISON_DB_URL)
    assert "APP_HOST" in str(exc.value)


@pytest.mark.parametrize("env", ["development", "staging"])
def test_an_unprovisioned_environment_without_a_database_refuses(
    clean_env, env
) -> None:
    with pytest.raises(ConfigurationError) as exc:
        build(APP_ENV=env, APP_HOST="10.0.0.1")
    assert "WRITER_DB_URL" in str(exc.value)


@pytest.mark.parametrize("env", ["development", "staging"])
def test_an_unprovisioned_environment_that_is_provisioned_starts(
    clean_env, env
) -> None:
    """`development` and `staging` are not forbidden — they are unbuilt. The day a
    domain is registered, turning one on is setting these two variables."""
    settings = build(APP_ENV=env, APP_HOST="10.0.0.1", WRITER_DB_URL=POISON_DB_URL)
    assert settings.APP_ENV is Environment(env)


def test_local_needs_no_host_or_database(clean_env) -> None:
    """The one environment that runs today runs with no configuration at all."""
    assert build(APP_ENV="local").APP_ENV is Environment.LOCAL


def test_production_refuses_the_default_signing_key(clean_env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        production(JWT_SECRET_KEY=DEFAULT_JWT_SECRET_KEY)
    assert "JWT_SECRET_KEY" in str(exc.value)


def test_production_refuses_debug_mode(clean_env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        production(DEBUG=True)
    assert "DEBUG" in str(exc.value)


def test_production_refuses_wildcard_cors_with_credentials(clean_env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        production(ALLOW_ORIGINS=["*"], ALLOW_CREDENTIALS=True)
    assert "ALLOW_ORIGINS" in str(exc.value)


def test_production_allows_a_wildcard_without_credentials(clean_env) -> None:
    """The refusal is about the *combination*. A wildcard with credentials off is a
    public read-only API, which is a coherent thing to deploy."""
    settings = production(ALLOW_ORIGINS=["*"], ALLOW_CREDENTIALS=False)
    assert settings.ALLOW_CREDENTIALS is False


# --------------------------------------------------------------------------- #
# The public-network scheme rule — the backend's instance of it
# --------------------------------------------------------------------------- #
#
# A URL a browser reaches over a public network is `https://` in every deployed
# environment. The two clients have carried that rule since #95 and #96; the backend
# carried none, so "the three apps agree" was false in the direction nobody was
# looking. `ALLOW_ORIGINS` is the only such URL the backend holds — it calls nothing
# over HTTP — and an `http://` entry is a browser origin served in the clear, which is
# the session cookie ADR-0007 puts in an httpOnly cookie travelling in the clear.


@pytest.mark.parametrize("env", ["development", "staging", "production"])
def test_a_deployed_environment_refuses_a_plaintext_browser_origin(
    clean_env, env: str
) -> None:
    with pytest.raises(ConfigurationError) as exc:
        settings_for(env, ALLOW_ORIGINS=["http://club.raketa.example"])
    assert "ALLOW_ORIGINS" in str(exc.value)


@pytest.mark.parametrize("env", ["development", "staging", "production"])
def test_a_deployed_environment_accepts_https_browser_origins(
    clean_env, env: str
) -> None:
    """The other half. A guard that fires on everything is not a guard."""
    origins = ["https://club.raketa.example", "https://admin.raketa.example"]
    assert settings_for(env, ALLOW_ORIGINS=origins).ALLOW_ORIGINS == origins


def test_one_plaintext_origin_among_several_is_enough_to_refuse(clean_env) -> None:
    """The check is over every entry, not over the first one.

    A list is exactly where this mistake hides: the reviewed line is `https://` and the
    one appended underneath it a month later is not.
    """
    with pytest.raises(ConfigurationError) as exc:
        production(
            ALLOW_ORIGINS=[
                "https://club.raketa.example",
                "http://staging-box.raketa.example",
            ]
        )
    assert "ALLOW_ORIGINS" in str(exc.value)


def test_local_accepts_a_plaintext_browser_origin(clean_env) -> None:
    """`http://localhost:3000` is what the club app actually serves on a laptop.

    The rule is about a *public network*; `local` is not one, which is the same reason
    both clients stopped constraining `local`'s scheme at all.
    """
    settings = build(APP_ENV="local", ALLOW_ORIGINS=["http://localhost:3000"])
    assert settings.ALLOW_ORIGINS == ["http://localhost:3000"]


def test_the_wildcard_is_not_read_as_a_plaintext_origin(clean_env) -> None:
    """`*` is not a URL, so the scheme rule has nothing to say about it.

    It has its own refusal — with credentials, in production — and reading it here as a
    non-https origin would refuse the credential-free public API that refusal
    deliberately permits.
    """
    settings = settings_for("staging", ALLOW_ORIGINS=["*"], ALLOW_CREDENTIALS=False)
    assert settings.ALLOW_ORIGINS == ["*"]


def test_the_scheme_refusal_does_not_echo_the_origin(clean_env) -> None:
    """It reports how many are wrong, never which. An origin can carry a hostname an
    operator would rather not have in a public crash report, and the rule the whole
    module follows is that a refusal names the variable, never the value."""
    origin = "http://internal-box.raketa.example:8443"

    with pytest.raises(ConfigurationError) as exc:
        production(ALLOW_ORIGINS=[origin])

    assert origin not in str(exc.value)
    assert "ALLOW_ORIGINS" in str(exc.value)


@pytest.mark.parametrize("mode", ["disable", "allow", ""])
def test_production_refuses_an_unencrypted_database(clean_env, mode: str) -> None:
    """`allow` is in the list because the database engine treats it exactly as
    `disable` — it returns the same `False` sentinel and opens the socket in the
    clear. A mode that reads as if it might encrypt and does not is worse than one
    that says `disable`."""
    with pytest.raises(ConfigurationError) as exc:
        production(DB_SSL_MODE=mode)
    assert "DB_SSL_MODE" in str(exc.value)


@pytest.mark.parametrize("mode", ["require", "verify-ca", "verify-full"])
def test_production_accepts_an_encrypted_database(clean_env, mode: str) -> None:
    assert production(DB_SSL_MODE=mode).DB_SSL_MODE == mode


def test_a_valid_production_configuration_starts(clean_env) -> None:
    """The other half of every refusal above. A guard that fires on everything is
    indistinguishable from a guard that fires on nothing, and neither is a guard."""
    settings = production()
    assert settings.APP_ENV is Environment.PRODUCTION
    assert settings.DEBUG is False
    assert settings.LOG_JSON is True


def test_no_refusal_fires_outside_the_environment_it_names(clean_env) -> None:
    """Every production trigger, in `local`, all at once — and it starts.

    This is the boundary the whole design rests on: the environment selects which
    *configuration* is dangerous, and a laptop with a wildcard CORS policy, debug on,
    the shipped signing key and an unencrypted database is a laptop working normally.
    """
    settings = build(
        APP_ENV="local",
        JWT_SECRET_KEY=DEFAULT_JWT_SECRET_KEY,
        DEBUG=True,
        ALLOW_ORIGINS=["*"],
        ALLOW_CREDENTIALS=True,
        DB_SSL_MODE="disable",
    )
    assert settings.APP_ENV is Environment.LOCAL


# --------------------------------------------------------------------------- #
# What a refusal is allowed to say
# --------------------------------------------------------------------------- #

#: Every refusal, each built so that a message leaking *any* configured value is
#: caught — not only the value that triggered this particular one.
REFUSALS = [
    ("APP_ENV", lambda: build(APP_ENV="prd", WRITER_DB_URL=POISON_DB_URL)),
    ("APP_HOST", lambda: build(APP_ENV="staging", WRITER_DB_URL=POISON_DB_URL)),
    ("WRITER_DB_URL", lambda: build(APP_ENV="staging", APP_HOST="10.0.0.1")),
    ("JWT_SECRET_KEY", lambda: production(JWT_SECRET_KEY=DEFAULT_JWT_SECRET_KEY)),
    ("DEBUG", lambda: production(DEBUG=True)),
    ("ALLOW_ORIGINS", lambda: production(ALLOW_ORIGINS=["*"])),
    (
        "ALLOW_ORIGINS",
        lambda: production(ALLOW_ORIGINS=[f"http://{POISON_PASSWORD}.example"]),
    ),
    ("DB_SSL_MODE", lambda: production(DB_SSL_MODE="disable")),
]

#: Two refusals name the same variable, so the ids are spelled rather than derived —
#: `ALLOW_ORIGINS0` in a failure report tells a reader nothing about which fired.
REFUSAL_IDS = [
    "APP_ENV",
    "APP_HOST",
    "WRITER_DB_URL",
    "JWT_SECRET_KEY",
    "DEBUG",
    "ALLOW_ORIGINS-wildcard-with-credentials",
    "ALLOW_ORIGINS-plaintext-when-deployed",
    "DB_SSL_MODE",
]


@pytest.mark.parametrize("variable, trigger", REFUSALS, ids=REFUSAL_IDS)
def test_every_refusal_names_its_variable(clean_env, variable, trigger) -> None:
    with pytest.raises(ConfigurationError) as exc:
        trigger()
    assert variable in str(exc.value), (
        "a refusal that does not name the variable makes fixing it a source-reading "
        "exercise"
    )


@pytest.mark.parametrize("variable, trigger", REFUSALS, ids=REFUSAL_IDS)
def test_no_refusal_echoes_a_value(clean_env, variable, trigger) -> None:
    with pytest.raises(ConfigurationError) as exc:
        trigger()
    message = str(exc.value)
    for leaked in (
        POISON_PASSWORD,
        POISON_DB_URL,
        POISON_SECRET,
        DEFAULT_JWT_SECRET_KEY,
        "prd",
    ):
        assert leaked not in message, f"{variable} refusal echoed a configured value"


def test_a_refusal_is_not_a_pydantic_validation_error(clean_env) -> None:
    """The reason `ConfigurationError` is not a `ValueError`.

    Pydantic wraps a `ValueError` raised inside a validator into a `ValidationError`
    whose repr carries `input_value=…` — for an after-validator, the entire settings
    object, signing key included. This test is what stops a later refactor "tidying"
    these into idiomatic pydantic validators and reintroducing the leak.
    """
    with pytest.raises(ConfigurationError) as exc:
        production(JWT_SECRET_KEY=DEFAULT_JWT_SECRET_KEY)
    assert not isinstance(exc.value, ValueError)
    assert "validation error" not in str(exc.value).lower()


# --------------------------------------------------------------------------- #
# Observability
# --------------------------------------------------------------------------- #


@pytest.fixture
def restore_root_logger():
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    root.handlers = handlers
    root.setLevel(level)


@pytest.mark.parametrize("env", list(Environment))
def test_every_structured_log_record_carries_its_environment(
    clean_env, restore_root_logger, env
) -> None:
    """A `development` crash must never be readable as a production incident."""
    settings = settings_for(env, LOG_JSON=True)
    configure_logging(settings)

    formatter = logging.getLogger().handlers[0].formatter
    record = logging.LogRecord(
        name="raketa.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="a thing happened",
        args=(),
        exc_info=None,
    )

    import json

    payload = json.loads(formatter.format(record))
    assert payload["env"] == env.value
