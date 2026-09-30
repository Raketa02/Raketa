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

from app.bootstrap.composition import build_password_hasher
from app.core.config import (
    DEFAULT_JWT_SECRET_KEY,
    DEFAULT_PHOTO_STORAGE_SECRET_KEY,
    DEPLOYED,
    ENVIRONMENT_PROFILES,
    PRODUCTION_BCRYPT_ROUNDS,
    ConfigurationError,
    Environment,
    Settings,
)
from app.core.logging import configure_logging
from tests.unit.bcrypt_cost import BCRYPT_MINIMUM_ROUNDS, cost_of

#: A password no legitimate message has any reason to contain.
POISON_PASSWORD = "hunter2-do-not-log-me"
POISON_DB_URL = f"postgresql+asyncpg://u:{POISON_PASSWORD}@db.example:5432/raketa"
POISON_SECRET = "s3cret-do-not-log-me"
POISON_PHOTO_SECRET = "photo-s3cret-do-not-log-me"
POISON_REDIS_URL = f"redis://:{POISON_PASSWORD}@redis.example:6379/0"
#: A public site on a host nobody should read in a crash report.
POISON_PUBLIC_SITE_URL = f"https://{POISON_PASSWORD}.raketa.example"
#: And the club website, the mail relay and the sender, likewise.
POISON_CLUB_WEBSITE_URL = f"https://{POISON_PASSWORD}.clubs.raketa.example"
POISON_SMTP_HOST = f"{POISON_PASSWORD}.smtp.example"
POISON_MAIL_SENDER = f"Raketa <no-reply@{POISON_PASSWORD}.example>"
#: Stripe keys, each carrying the poison: a test key a laptop and a rehearsal
#: hold, the live key only production may, and the publishable and webhook
#: secrets beside them.
POISON_STRIPE_TEST_KEY = f"sk_test_{POISON_PASSWORD}"
POISON_STRIPE_LIVE_KEY = f"sk_live_{POISON_PASSWORD}"
POISON_STRIPE_PUBLISHABLE_KEY = f"pk_test_{POISON_PASSWORD}"
POISON_STRIPE_WEBHOOK_SECRET = f"whsec_{POISON_PASSWORD}"

#: What every deployed environment has to supply because its shipped default is
#: a laptop's: three addresses out of `docker-compose-local.yml`, the two web
#: apps' dev servers, the local mail catcher and its reserved-domain sender — and
#: an encrypted connection to the relay, which is a value rather than a presence.
DEPLOYED_ADDRESSES = {
    "APP_HOST": "10.0.0.1",
    "WRITER_DB_URL": POISON_DB_URL,
    "REDIS_URL": POISON_REDIS_URL,
    "PUBLIC_SITE_URL": POISON_PUBLIC_SITE_URL,
    "CLUB_WEBSITE_URL": POISON_CLUB_WEBSITE_URL,
    "SMTP_HOST": POISON_SMTP_HOST,
    "MAIL_SENDER": POISON_MAIL_SENDER,
}
DEPLOYED_MAIL_SECURITY = {"SMTP_SECURITY": "starttls"}
#: What every deployed environment supplies for payments: Stripe, with all three
#: of its secrets. Production swaps the test key for the live one.
DEPLOYED_PAYMENTS = {
    "PAYMENTS_PROVIDER": "stripe",
    "STRIPE_SECRET_KEY": POISON_STRIPE_TEST_KEY,
    "STRIPE_PUBLISHABLE_KEY": POISON_STRIPE_PUBLISHABLE_KEY,
    "STRIPE_WEBHOOK_SECRET": POISON_STRIPE_WEBHOOK_SECRET,
}


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
    laptop needs nothing, anything deployed needs the addresses whose shipped
    defaults are the dev stack's own (``DEPLOYED_ADDRESSES``) and an encrypted mail
    relay — and production needs those plus the four things it refuses to start
    with the shipped value of.
    """
    env = Environment(env)
    base: dict = {"APP_ENV": env}
    if env in DEPLOYED:
        base |= DEPLOYED_ADDRESSES | DEPLOYED_MAIL_SECURITY | DEPLOYED_PAYMENTS
    if env is Environment.PRODUCTION:
        base |= {
            "STRIPE_SECRET_KEY": POISON_STRIPE_LIVE_KEY,
            "JWT_SECRET_KEY": POISON_SECRET,
            "PHOTO_STORAGE_SECRET_KEY": POISON_PHOTO_SECRET,
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


#: Every environment the three presence refusals hold for. Spelled out rather than
#: derived from `DEPLOYED`, because a set that quietly lost a member would quietly
#: stop being asserted about — the parametrisation is what makes the loss visible.
DEPLOYED_NAMES = ["development", "staging", "production"]


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_without_a_host_refuses(clean_env, env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        build(APP_ENV=env, WRITER_DB_URL=POISON_DB_URL)
    assert "APP_HOST" in str(exc.value)


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_without_a_database_refuses(clean_env, env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        build(APP_ENV=env, APP_HOST="10.0.0.1")
    assert "WRITER_DB_URL" in str(exc.value)


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_without_an_ephemeral_store_refuses(
    clean_env, env
) -> None:
    """The ledgers fail soft; booting permanently degraded is not the same thing.

    An unreachable Redis costs a search its spread and costs nobody their place in
    it — which is exactly why this has to refuse rather than shrug: a ledger that
    never works produces no error, no empty screen and no alarm, and looks from
    every angle like a city where nothing happened.

    **`production` is in this list, and used not to be** (#341). While the three
    refusals were stated over the unbuilt two alone, the one environment where a
    laptop's service name costs the most was the one that could inherit it — and
    the committed ECS task definition did exactly that.
    """

    with pytest.raises(ConfigurationError) as exc:
        build(APP_ENV=env, APP_HOST="10.0.0.1", WRITER_DB_URL=POISON_DB_URL)
    assert "REDIS_URL" in str(exc.value)


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_inherits_no_local_address(clean_env, env) -> None:
    """The rule under all three, stated once: nothing deployed may *silently* end up
    holding a value out of `docker-compose-local.yml`.

    Asserted as "the refusal names it" rather than "the value differs from the
    default", because the settings object asks whether somebody set it — a deployed
    environment that deliberately configured the laptop's address is somebody's
    decision, and an empty variable is nobody's.
    """
    for missing in DEPLOYED_ADDRESSES:
        supplied = DEPLOYED_ADDRESSES | DEPLOYED_MAIL_SECURITY
        del supplied[missing]
        with pytest.raises(ConfigurationError) as exc:
            build(APP_ENV=env, **supplied)
        assert missing in str(exc.value)


def test_local_needs_no_ephemeral_store_configured(clean_env) -> None:
    """The one environment that runs today runs against the dev stack's Redis."""

    from app.core.config import DEFAULT_REDIS_URL

    assert build(APP_ENV="local").REDIS_URL == DEFAULT_REDIS_URL


@pytest.mark.parametrize("env", ["development", "staging"])
def test_an_unprovisioned_environment_that_is_provisioned_starts(
    clean_env, env
) -> None:
    """`development` and `staging` are not forbidden — they are unbuilt. The day a
    domain is registered, turning one on is setting these variables.

    Still only the unbuilt two: `production` is covered by
    `test_a_valid_production_configuration_starts`, which has four more things to
    supply before it gets an answer."""
    settings = build(
        APP_ENV=env,
        **DEPLOYED_ADDRESSES,
        **DEPLOYED_MAIL_SECURITY,
        **DEPLOYED_PAYMENTS,
    )
    assert settings.APP_ENV is Environment(env)


def test_local_needs_no_host_or_database(clean_env) -> None:
    """The one environment that runs today runs with no configuration at all."""
    assert build(APP_ENV="local").APP_ENV is Environment.LOCAL


def test_production_refuses_the_default_signing_key(clean_env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        production(JWT_SECRET_KEY=DEFAULT_JWT_SECRET_KEY)
    assert "JWT_SECRET_KEY" in str(exc.value)


def test_production_refuses_the_shipped_photo_storage_secret(clean_env) -> None:
    """The same failure as the signing key, on the bucket holding players' faces.

    It is the local MinIO container's password, written in the compose file and
    in both templates, so it is as public as the signing key — and it grants
    read and write over every photo the platform holds.
    """
    with pytest.raises(ConfigurationError) as exc:
        production(PHOTO_STORAGE_SECRET_KEY=DEFAULT_PHOTO_STORAGE_SECRET_KEY)
    assert "PHOTO_STORAGE_SECRET_KEY" in str(exc.value)


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
# looking. The backend calls nothing over HTTP and holds two such URLs: an `http://`
# entry in `ALLOW_ORIGINS` is a browser origin served in the clear, which is the session
# cookie ADR-0007 puts in an httpOnly cookie travelling in the clear; and
# `PUBLIC_SITE_URL` is the address every group link is printed under (#504).


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


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_refuses_a_plaintext_public_site(clean_env, env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        settings_for(env, PUBLIC_SITE_URL="http://raketa.example")
    assert "PUBLIC_SITE_URL" in str(exc.value)


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_accepts_an_https_public_site(clean_env, env) -> None:
    site = "https://raketa.example"
    assert settings_for(env, PUBLIC_SITE_URL=site).PUBLIC_SITE_URL == site


def test_local_links_to_the_public_site_s_dev_server(clean_env) -> None:
    """The one environment that runs today needs no public site configured, and
    its links are plaintext because a laptop is not a public network."""

    from app.core.config import DEFAULT_PUBLIC_SITE_URL

    assert build(APP_ENV="local").PUBLIC_SITE_URL == DEFAULT_PUBLIC_SITE_URL
    assert DEFAULT_PUBLIC_SITE_URL.startswith("http://localhost")


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_refuses_a_plaintext_club_website(
    clean_env, env
) -> None:
    """A club's reset link is printed under it and opened over a public network."""

    with pytest.raises(ConfigurationError) as exc:
        settings_for(env, CLUB_WEBSITE_URL="http://clubs.raketa.example")
    assert "CLUB_WEBSITE_URL" in str(exc.value)


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_refuses_mail_in_the_clear(clean_env, env) -> None:
    """Every reset and invitation carries a code that opens an account
    (``docs/adr/0186`` §1), so the relay is reached over TLS once deployed."""

    with pytest.raises(ConfigurationError) as exc:
        settings_for(env, SMTP_SECURITY="none")
    assert "SMTP_SECURITY" in str(exc.value)


@pytest.mark.parametrize("security", ["starttls", "tls"])
@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_accepts_an_encrypted_relay(
    clean_env, env, security
) -> None:
    assert settings_for(env, SMTP_SECURITY=security).SMTP_SECURITY == security


def test_local_mails_the_catcher_and_links_to_the_club_website_s_dev_server(
    clean_env,
) -> None:
    """A laptop's email lands in the dev stack's mail catcher, in the clear,
    from a reserved domain — and none of that is a refusal there."""

    from app.core.config import (
        DEFAULT_CLUB_WEBSITE_URL,
        DEFAULT_MAIL_SENDER,
        DEFAULT_SMTP_HOST,
    )

    settings = build(APP_ENV="local")
    assert settings.SMTP_HOST == DEFAULT_SMTP_HOST == "mailpit"
    assert settings.SMTP_SECURITY == "none"
    assert settings.MAIL_SENDER == DEFAULT_MAIL_SENDER
    assert settings.CLUB_WEBSITE_URL == DEFAULT_CLUB_WEBSITE_URL
    assert DEFAULT_CLUB_WEBSITE_URL.startswith("http://localhost")


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
        PHOTO_STORAGE_SECRET_KEY=DEFAULT_PHOTO_STORAGE_SECRET_KEY,
        DEBUG=True,
        ALLOW_ORIGINS=["*"],
        ALLOW_CREDENTIALS=True,
        DB_SSL_MODE="disable",
        BCRYPT_ROUNDS=BCRYPT_MINIMUM_ROUNDS,
    )
    assert settings.APP_ENV is Environment.LOCAL


# --------------------------------------------------------------------------- #
# Payments
# --------------------------------------------------------------------------- #
#
# Which provider money moves through is configuration, and three of its
# configurations are dangerous rather than wrong: a deployed environment on the
# fake books games nobody paid for, a live key off production is a laptop one
# setting away from charging real cards, and a test key in production is the
# fake again in a different coat.


def test_a_laptop_moves_money_through_the_fake(clean_env) -> None:
    """No key, no network, nothing leaves the machine — and no refusal."""
    assert build(APP_ENV="local").PAYMENTS_PROVIDER == "fake"


@pytest.mark.parametrize("env", sorted(DEPLOYED))
def test_a_deployed_environment_refuses_the_fake(clean_env, env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        settings_for(env, PAYMENTS_PROVIDER="fake")
    assert "PAYMENTS_PROVIDER" in str(exc.value)


@pytest.mark.parametrize("missing", ["STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY"])
def test_stripe_without_its_keys_refuses_even_on_a_laptop(clean_env, missing) -> None:
    keys = {
        "STRIPE_SECRET_KEY": POISON_STRIPE_TEST_KEY,
        "STRIPE_PUBLISHABLE_KEY": POISON_STRIPE_PUBLISHABLE_KEY,
    }
    del keys[missing]
    with pytest.raises(ConfigurationError) as exc:
        build(APP_ENV="local", PAYMENTS_PROVIDER="stripe", **keys)
    assert missing in str(exc.value)


def test_a_laptop_may_run_stripe_without_a_webhook_secret(clean_env) -> None:
    """Its platform endpoint then answers every event with 503, which is honest
    about a laptop nobody pointed ``stripe listen`` at."""
    settings = build(
        APP_ENV="local",
        PAYMENTS_PROVIDER="stripe",
        STRIPE_SECRET_KEY=POISON_STRIPE_TEST_KEY,
        STRIPE_PUBLISHABLE_KEY=POISON_STRIPE_PUBLISHABLE_KEY,
    )
    assert settings.STRIPE_WEBHOOK_SECRET is None


@pytest.mark.parametrize("env", sorted(DEPLOYED))
def test_a_deployed_environment_verifies_every_webhook(clean_env, env) -> None:
    with pytest.raises(ConfigurationError) as exc:
        settings_for(env, STRIPE_WEBHOOK_SECRET=None)
    assert "STRIPE_WEBHOOK_SECRET" in str(exc.value)


@pytest.mark.parametrize(
    "env", [Environment.LOCAL, Environment.DEVELOPMENT, Environment.STAGING]
)
@pytest.mark.parametrize("prefix", ["sk_live_", "rk_live_"])
def test_only_production_may_hold_a_live_key(clean_env, env, prefix) -> None:
    """Whichever provider is selected — a live key sitting unused in a laptop's
    ``.env`` is one setting away from a test run charging real cards."""
    with pytest.raises(ConfigurationError) as exc:
        settings_for(env, STRIPE_SECRET_KEY=f"{prefix}{POISON_PASSWORD}")
    assert "STRIPE_SECRET_KEY" in str(exc.value)


@pytest.mark.parametrize("prefix", ["sk_test_", "rk_test_"])
def test_production_refuses_a_test_key(clean_env, prefix) -> None:
    with pytest.raises(ConfigurationError) as exc:
        production(STRIPE_SECRET_KEY=f"{prefix}{POISON_PASSWORD}")
    assert "STRIPE_SECRET_KEY" in str(exc.value)


def test_production_runs_on_the_live_key(clean_env) -> None:
    settings = production()
    assert settings.PAYMENTS_PROVIDER == "stripe"
    assert settings.STRIPE_SECRET_KEY == POISON_STRIPE_LIVE_KEY


# --------------------------------------------------------------------------- #
# The work factor
# --------------------------------------------------------------------------- #
#
# Why it is a setting at all is argued beside `BCRYPT_ROUNDS` in the settings
# module. What is asserted here is the half that makes lowering it safe: nothing
# deployed may.


@pytest.mark.parametrize("env", list(Environment))
def test_every_environment_hashes_at_production_strength_by_default(
    clean_env, env
) -> None:
    """One default, and it is production's. The environment selects no work
    factor; a laptop that wants a cheaper one says so."""
    assert settings_for(env).BCRYPT_ROUNDS == PRODUCTION_BCRYPT_ROUNDS == 12


def test_a_hash_made_under_production_configuration_carries_production_strength(
    clean_env,
) -> None:
    """Read off the hash itself, because that is the only place the cost the
    adapter actually used is recorded — a setting could say twelve while the
    adapter ignored it."""
    hasher = build_password_hasher(production())

    assert cost_of(hasher.hash("hunter22!")) == 12


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
@pytest.mark.parametrize("rounds", range(BCRYPT_MINIMUM_ROUNDS, 12))
def test_a_deployed_environment_refuses_a_weaker_work_factor(
    clean_env, env, rounds: int
) -> None:
    """Every value bcrypt accepts below production's, in every deployed
    environment — and the message names the variable and never the number.

    A weak work factor is dangerous rather than merely wrong: nothing fails, every
    login still works, and the stored hashes are simply cheaper to crack for as
    long as nobody looks.
    """
    with pytest.raises(ConfigurationError) as exc:
        settings_for(env, BCRYPT_ROUNDS=rounds)

    message = str(exc.value)
    assert "BCRYPT_ROUNDS" in message
    assert str(rounds) not in message


@pytest.mark.parametrize("env", DEPLOYED_NAMES)
def test_a_deployed_environment_accepts_a_stronger_work_factor(clean_env, env) -> None:
    """The other half. The floor is production's strength, not its ceiling."""
    assert settings_for(env, BCRYPT_ROUNDS=13).BCRYPT_ROUNDS == 13


def test_local_accepts_bcrypts_minimum(clean_env) -> None:
    """The test configuration's value. A laptop may hash as cheaply as the
    library allows, because nothing it stores is anybody's password."""
    settings = build(APP_ENV="local", BCRYPT_ROUNDS=BCRYPT_MINIMUM_ROUNDS)
    assert settings.BCRYPT_ROUNDS == BCRYPT_MINIMUM_ROUNDS


# --------------------------------------------------------------------------- #
# What a refusal is allowed to say
# --------------------------------------------------------------------------- #

#: Every refusal, each built so that a message leaking *any* configured value is
#: caught — not only the value that triggered this particular one.
REFUSALS = [
    ("APP_ENV", lambda: build(APP_ENV="prd", WRITER_DB_URL=POISON_DB_URL)),
    ("APP_HOST", lambda: build(APP_ENV="staging", WRITER_DB_URL=POISON_DB_URL)),
    ("WRITER_DB_URL", lambda: build(APP_ENV="staging", APP_HOST="10.0.0.1")),
    (
        "REDIS_URL",
        lambda: build(
            APP_ENV="staging", APP_HOST="10.0.0.1", WRITER_DB_URL=POISON_DB_URL
        ),
    ),
    # The same three in production. Not redundant: production reaches them through
    # a different branch than it used to, and these are the messages a deploy of the
    # ECS task definition would actually print into CloudWatch.
    (
        "PUBLIC_SITE_URL",
        lambda: build(
            APP_ENV="staging",
            APP_HOST="10.0.0.1",
            WRITER_DB_URL=POISON_DB_URL,
            REDIS_URL=POISON_REDIS_URL,
        ),
    ),
    ("APP_HOST", lambda: build(APP_ENV="production", WRITER_DB_URL=POISON_DB_URL)),
    ("WRITER_DB_URL", lambda: build(APP_ENV="production", APP_HOST="10.0.0.1")),
    (
        "REDIS_URL",
        lambda: build(
            APP_ENV="production", APP_HOST="10.0.0.1", WRITER_DB_URL=POISON_DB_URL
        ),
    ),
    ("JWT_SECRET_KEY", lambda: production(JWT_SECRET_KEY=DEFAULT_JWT_SECRET_KEY)),
    (
        "PHOTO_STORAGE_SECRET_KEY",
        lambda: production(
            PHOTO_STORAGE_SECRET_KEY=DEFAULT_PHOTO_STORAGE_SECRET_KEY
        ),
    ),
    ("DEBUG", lambda: production(DEBUG=True)),
    ("ALLOW_ORIGINS", lambda: production(ALLOW_ORIGINS=["*"])),
    (
        "ALLOW_ORIGINS",
        lambda: production(ALLOW_ORIGINS=[f"http://{POISON_PASSWORD}.example"]),
    ),
    (
        "PUBLIC_SITE_URL",
        lambda: production(PUBLIC_SITE_URL=f"http://{POISON_PASSWORD}.example"),
    ),
    ("DB_SSL_MODE", lambda: production(DB_SSL_MODE="disable")),
    (
        "CLUB_WEBSITE_URL",
        lambda: build(
            APP_ENV="staging",
            **{
                k: v
                for k, v in DEPLOYED_ADDRESSES.items()
                if k != "CLUB_WEBSITE_URL"
            },
        ),
    ),
    (
        "SMTP_HOST",
        lambda: build(
            APP_ENV="production",
            **{k: v for k, v in DEPLOYED_ADDRESSES.items() if k != "SMTP_HOST"},
        ),
    ),
    (
        "MAIL_SENDER",
        lambda: build(
            APP_ENV="production",
            **{k: v for k, v in DEPLOYED_ADDRESSES.items() if k != "MAIL_SENDER"},
        ),
    ),
    (
        "CLUB_WEBSITE_URL",
        lambda: production(CLUB_WEBSITE_URL=f"http://{POISON_PASSWORD}.example"),
    ),
    ("SMTP_SECURITY", lambda: production(SMTP_SECURITY="none")),
    (
        "BCRYPT_ROUNDS",
        lambda: settings_for("staging", BCRYPT_ROUNDS=BCRYPT_MINIMUM_ROUNDS),
    ),
    ("BCRYPT_ROUNDS", lambda: production(BCRYPT_ROUNDS=BCRYPT_MINIMUM_ROUNDS)),
    ("PAYMENTS_PROVIDER", lambda: production(PAYMENTS_PROVIDER="fake")),
    (
        "STRIPE_SECRET_KEY",
        lambda: settings_for("staging", STRIPE_SECRET_KEY=None),
    ),
    (
        "STRIPE_WEBHOOK_SECRET",
        lambda: production(STRIPE_WEBHOOK_SECRET=None),
    ),
    (
        "STRIPE_SECRET_KEY",
        lambda: settings_for("staging", STRIPE_SECRET_KEY=POISON_STRIPE_LIVE_KEY),
    ),
    (
        "STRIPE_SECRET_KEY",
        lambda: production(STRIPE_SECRET_KEY=POISON_STRIPE_TEST_KEY),
    ),
]

#: Several refusals name the same variable, so the ids are spelled rather than derived —
#: `ALLOW_ORIGINS0` in a failure report tells a reader nothing about which fired.
REFUSAL_IDS = [
    "APP_ENV",
    "APP_HOST",
    "WRITER_DB_URL",
    "REDIS_URL",
    "PUBLIC_SITE_URL",
    "APP_HOST-in-production",
    "WRITER_DB_URL-in-production",
    "REDIS_URL-in-production",
    "JWT_SECRET_KEY",
    "PHOTO_STORAGE_SECRET_KEY",
    "DEBUG",
    "ALLOW_ORIGINS-wildcard-with-credentials",
    "ALLOW_ORIGINS-plaintext-when-deployed",
    "PUBLIC_SITE_URL-plaintext-when-deployed",
    "DB_SSL_MODE",
    "CLUB_WEBSITE_URL",
    "SMTP_HOST-in-production",
    "MAIL_SENDER-in-production",
    "CLUB_WEBSITE_URL-plaintext-when-deployed",
    "SMTP_SECURITY-none-in-production",
    "BCRYPT_ROUNDS",
    "BCRYPT_ROUNDS-in-production",
    "PAYMENTS_PROVIDER-fake-in-production",
    "STRIPE_SECRET_KEY-missing",
    "STRIPE_WEBHOOK_SECRET-missing-in-production",
    "STRIPE_SECRET_KEY-live-off-production",
    "STRIPE_SECRET_KEY-test-in-production",
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
        POISON_REDIS_URL,
        POISON_PUBLIC_SITE_URL,
        POISON_CLUB_WEBSITE_URL,
        POISON_SMTP_HOST,
        POISON_MAIL_SENDER,
        POISON_STRIPE_TEST_KEY,
        POISON_STRIPE_LIVE_KEY,
        POISON_STRIPE_PUBLISHABLE_KEY,
        POISON_STRIPE_WEBHOOK_SECRET,
        POISON_SECRET,
        POISON_PHOTO_SECRET,
        DEFAULT_JWT_SECRET_KEY,
        DEFAULT_PHOTO_STORAGE_SECRET_KEY,
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
