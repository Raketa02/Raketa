"""Application configuration: one enum decides the profile, and dangerous
configuration refuses to start.

Two rules govern this module.

**The environment may select configuration defaults; it may never select behaviour a
domain test could observe.** No deadline, threshold, validation, status code or response
shape varies by `APP_ENV`. What it does select is the handful of settings that always
move together — debug mode, log level, log format — which were previously independent
knobs kept in agreement by memory. One value replaces three, and the failure mode it
removes is the silent one: nothing goes wrong until the deployment where somebody sets
two of them and forgets the third.

**Configuration that is dangerous rather than merely wrong refuses to boot.** The
refusals are checked on the settings object itself rather than in the application
factory, so they hold for every construction path — a worker, a migration, a seed run —
and not only for a process that happens to serve HTTP.

Every refusal names the offending variable and the reason, and **never echoes the
offending value**: a `WRITER_DB_URL` carries a password, and a refusal message goes
straight into a log aggregator or a crash report. The environment name appears in
messages where it is the *reason* — it is not a secret, and it is already on every log
record — but it is never the offending value of the refusal that prints it.
"""

import json
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Any, List, Optional, Set

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Environment(StrEnum):
    """The four environments, named identically by all three apps.

    `local` is a developer's own machine and is the only one that runs today.
    `development` and `staging` are defined and validated but **not provisioned** — no
    domain is registered, so selecting one is a startup failure naming the missing
    variable rather than a silent fallback to something that happens to be reachable.

    A `StrEnum` rather than a bare `Enum` so that a comparison against the spelling
    still works and `json.dumps` writes the name straight onto a log record. The bug
    this closes is not the comparison, it is the *unconstrained input*: the old field
    was a free string defaulting to `dev`, so `prd` was accepted silently and made a
    production deployment behave as non-production.
    """

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


#: Spelled once, for refusal messages and for the environment template.
ENVIRONMENT_NAMES = ", ".join(e.value for e in Environment)


class ConfigurationError(RuntimeError):
    """The process refuses to start because its configuration is dangerous.

    Deliberately **not** a `ValueError`: pydantic wraps `ValueError` raised inside a
    validator into a `ValidationError` whose repr includes `input_value=…`, which for an
    after-validator is the whole settings object — every secret in it. Any other
    exception type propagates unwrapped, so the message below is the whole message.
    """


@dataclass(frozen=True)
class EnvironmentProfile:
    """The settings `APP_ENV` supplies defaults for. Each stays overridable."""

    DEBUG: bool
    LOG_LEVEL: str
    LOG_JSON: bool


#: The profile table. `local` is a laptop, so it gets readable logs and debug mode;
#: everything deployed is ingested by a log aggregator, so it gets JSON. `development`
#: keeps DEBUG-level verbosity because it exists to be debugged; `staging` matches
#: production, because that is what makes it a rehearsal.
ENVIRONMENT_PROFILES = {
    Environment.LOCAL: EnvironmentProfile(
        DEBUG=True, LOG_LEVEL="DEBUG", LOG_JSON=False
    ),
    Environment.DEVELOPMENT: EnvironmentProfile(
        DEBUG=False, LOG_LEVEL="DEBUG", LOG_JSON=True
    ),
    Environment.STAGING: EnvironmentProfile(
        DEBUG=False, LOG_LEVEL="INFO", LOG_JSON=True
    ),
    Environment.PRODUCTION: EnvironmentProfile(
        DEBUG=False, LOG_LEVEL="INFO", LOG_JSON=True
    ),
}

#: The environments that must be explicitly provisioned before they can be selected.
#: Neither exists yet, which is exactly why choosing one has to fail loudly.
UNPROVISIONED = frozenset({Environment.DEVELOPMENT, Environment.STAGING})

#: `DB_SSL_MODE` values that actually encrypt the connection. `disable` and `allow` do
#: not — see `_build_db_ssl_context` in the database engine, which returns `False` for
#: both, meaning asyncpg opens the socket in the clear.
ENCRYPTED_DB_SSL_MODES = frozenset({"require", "verify-ca", "verify-full"})

#: The shipped placeholder. In production it is the single most damaging configuration
#: mistake available: it is in this file, in both templates, and in git history.
DEFAULT_JWT_SECRET_KEY = "change-me-in-production"

#: The shipped object-store credentials. They are the MinIO container's, written in
#: `docker-compose-local.yml` and in both templates, so they are as public as the JWT
#: default above — and they unlock every photo the platform holds.
DEFAULT_PHOTO_STORAGE_ACCESS_KEY = "raketa_photos"
DEFAULT_PHOTO_STORAGE_SECRET_KEY = "raketa_photos_pwd"

#: The shipped ephemeral-store address. `redis` is the service name in
#: `docker-compose-local.yml`, so this default resolves on a laptop running the dev
#: stack and resolves nowhere else — which is what makes it safe to refuse rather
#: than fall back on, exactly as the writer database's default is.
DEFAULT_REDIS_URL = "redis://redis:6379/0"

#: The environments a browser reaches over a public network. `local` is not one of them,
#: which is what makes `http://localhost:3000` a legal allowed origin on a laptop.
DEPLOYED = frozenset(
    {Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION}
)

#: The CORS wildcard. Not an origin, so the scheme rule below has nothing to say about
#: it — it is governed by its own refusal, in combination with `ALLOW_CREDENTIALS`.
CORS_WILDCARD = "*"


class Settings(BaseSettings):
    # --- app metadata
    TITLE: str = "Raketa API"
    DESCRIPTION: str = "Production-ready Raketa backend with auth"
    VERSION: str = "1.0.0"

    # --- environment
    #
    # `APP_ENV`, not `ENV`: the old name collides with an ordinary shell variable, so a
    # value inherited from the surrounding environment could decide what environment the
    # application thought it was in.
    APP_ENV: Environment = Environment.LOCAL
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # --- derived from APP_ENV when not set explicitly (see ENVIRONMENT_PROFILES)
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # --- database
    WRITER_DB_URL: str = (
        "postgresql+asyncpg://raketa_user:raketa_pwd@db:5432/raketa"
    )
    READER_DB_URL: Optional[str] = None
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # --- db SSL
    DB_SSL_MODE: str = "disable"  # disable | require | verify-ca | verify-full
    DB_SSL_ROOT_CERT_PATH: Optional[str] = None
    DB_SSL_CLIENT_CERT_PATH: Optional[str] = None
    DB_SSL_CLIENT_KEY_PATH: Optional[str] = None

    # --- JWT
    JWT_SECRET_KEY: str = DEFAULT_JWT_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "raketa"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 900
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400

    # --- CORS
    ALLOW_ORIGINS: Annotated[List[str], NoDecode] = ["*"]
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: Annotated[List[str], NoDecode] = ["*"]
    ALLOW_HEADERS: Annotated[List[str], NoDecode] = ["*"]

    # --- external SSL
    EXTERNAL_SSL_ROOT_CA_PATH: Optional[str] = None
    CLIENT_CERT_PATH: Optional[str] = None
    CLIENT_KEY_PATH: Optional[str] = None
    SERVER_CERT_PATH: Optional[str] = None
    SERVER_KEY_PATH: Optional[str] = None
    ENABLE_MTLS: bool = False

    # --- migrations
    RUN_MIGRATIONS_ON_STARTUP: bool = False

    # --- photo storage (S3-compatible: MinIO locally, S3 deployed — docs/adr/0091)
    #
    # `PHOTO_STORAGE_ENDPOINT_URL` is a **server-to-server** URL and carries no scheme
    # rule; `PHOTO_STORAGE_PUBLIC_ENDPOINT_URL` is the one a player's phone opens a
    # presigned URL against, and falls back to the first when unset. Both are `None` in
    # a deployed environment, where botocore resolves AWS's own https endpoints — which
    # is the whole of the adapter swap.
    PHOTO_STORAGE_ENDPOINT_URL: Optional[str] = "http://minio:9000"
    PHOTO_STORAGE_PUBLIC_ENDPOINT_URL: Optional[str] = None
    PHOTO_STORAGE_BUCKET: str = "raketa-player-photos"
    PHOTO_STORAGE_REGION: str = "us-east-1"
    PHOTO_STORAGE_ACCESS_KEY: str = DEFAULT_PHOTO_STORAGE_ACCESS_KEY
    PHOTO_STORAGE_SECRET_KEY: str = DEFAULT_PHOTO_STORAGE_SECRET_KEY
    #: How long a presigned photo URL works for. Whole minutes, because that is the
    #: unit the kernel's clock arithmetic takes and the window is not a precise
    #: quantity — it is *short enough that a leaked URL stops being one*.
    PHOTO_URL_VALID_FOR_MINUTES: int = 5

    # --- the on-court photo check (docs/adr/0129)
    #
    # **Where the checker is and how long it may take are configuration; what it
    # asks and where the line sits are not.** The prompt set and the threshold
    # are behaviour a domain test can observe — a photo flagged on a laptop and
    # allowed in production would be exactly the thing this module's first rule
    # forbids — so they live in `app/modules/player_profile/domain/photos.py` and
    # cannot be set from the environment. Neither setting below can change a
    # verdict; they can only decide whether one is reached.
    #
    # A server-to-server URL, like `PHOTO_STORAGE_ENDPOINT_URL` and carrying no
    # scheme rule for the same reason: no browser and no phone ever opens it.
    PHOTO_REVIEW_ENDPOINT_URL: str = "http://photo-review:8000"
    #: The whole budget for one review, connection included. Generous, because
    #: the far side is CPU inference on an image and a timeout costs a photo its
    #: verdict; bounded, because it sits inline on the upload request and an
    #: unbounded wait would hold the connection open for as long as the sidecar
    #: was wedged. Exceeding it is not an error a player sees — the adapter fails
    #: open and records that it did.
    PHOTO_REVIEW_TIMEOUT_SECONDS: float = 10.0

    # --- domain event delivery
    EVENT_DELIVERY_WORKER_ENABLED: bool = True
    EVENT_DELIVERY_POLL_INTERVAL_SECONDS: float = 1.0
    EVENT_DELIVERY_BATCH_SIZE: int = 100

    # --- scheduled jobs (docs/adr/0092)
    #
    # **How often the sweep runs is configuration; how old a photo must be before it
    # sweeps one is not.** The retention window is a rule a domain test can observe
    # and lives in `player_profile/domain/photos.py`; the cadence is operational and
    # belongs here. Turning the job off changes nothing a domain test would see —
    # orphans simply accumulate, which is the state the platform was in before it
    # existed.
    #
    # Six hours rather than a day, because the window is a *promise about how long an
    # orphan lives* and a daily cadence would stretch a 24-hour promise to 48. It is
    # a full listing of the photo prefix each time — the S3 API has no server-side
    # filter on `LastModified` — which is what keeps this in hours and not minutes.
    PHOTO_SWEEP_ENABLED: bool = True
    PHOTO_SWEEP_INTERVAL_SECONDS: float = 6 * 60 * 60

    # --- the photo re-review backfill (docs/adr/0132)
    #
    # **Not one of these can change which photos get re-reviewed.** That is read
    # off the note the object already carries (`player_profile/domain/photos.py`
    # — `review_standing`), so what is left here is operational: how often to
    # look, how much inference one run may spend, and how far apart to space it.
    # Turning the job off changes nothing a domain test could observe — the
    # unreviewed population simply stops shrinking, which is the state the
    # platform was in before the job existed.
    #
    # **Deliberately slow, and the cadence is in hours for the reason the
    # sweep's is.** A run is a walk of the whole photo prefix — and a `HEAD` per
    # object, because no S3-compatible listing carries user metadata — so the
    # cost of a *tick* is paid against the corpus whether or not there is
    # anything left to review. An hour puts that walk at six times the sweep's
    # and no more.
    #
    # The budget is what the *sidecar* is protected by: one container running a
    # single worker by design, with a live upload path queueing behind whatever
    # it is doing, and a second of quiet between asks so an upload is never
    # behind a hundred of them. A hundred an hour per API process drains any
    # backlog this platform has in days, and nothing is waiting on it — the
    # pass-through population is fixed and only shrinks, and the sweep already
    # removes the photos no profile ever committed.
    PHOTO_REVIEW_BACKFILL_ENABLED: bool = True
    PHOTO_REVIEW_BACKFILL_INTERVAL_SECONDS: float = 60 * 60
    PHOTO_REVIEW_BACKFILL_BATCH_LIMIT: int = 100
    PHOTO_REVIEW_BACKFILL_PAUSE_SECONDS: float = 1.0

    # --- the candidate index (docs/adr/0110, docs/adr/0112)
    #
    # **Two loops with two different jobs, and both cadences are configuration.**
    # The tail reader folds the log into the index; the snapshot refresh rebuilds
    # this worker's containers from what moved. Turning either off changes no
    # rule a domain test could observe — the index simply stops moving, which is
    # the state the platform was in before it existed.
    #
    # **What is emphatically not here is the staleness ladder.** Serve under
    # 15 minutes, flag to 24 hours, refuse past it — those live in
    # `matchmaking/domain/index_staleness.py`, because a refusal the environment
    # could switch off is a rule that is true on a laptop and false in
    # production. The two must not swap places, exactly as the photo sweep's
    # retention window and cadence must not.
    CANDIDATE_INDEX_ENABLED: bool = True
    #: The cadence `EventWorker` already runs at, so no new number is invented.
    #: Its falsifier is batches consistently hitting the bound below.
    CANDIDATE_INDEX_TAIL_INTERVAL_SECONDS: float = 1.0
    #: §17's p50 index-staleness target, matched directly.
    CANDIDATE_INDEX_REFRESH_INTERVAL_SECONDS: float = 2.0
    #: How many log rows one tick may look at, so a projection restarted against
    #: a long log does bounded work per tick rather than one huge transaction.
    CANDIDATE_INDEX_BATCH_SIZE: int = 500

    # --- the ephemeral store (docs/adr/0093)
    #
    # **Redis holds the two ledgers that are allowed to be lossy** — exposure and
    # suppression — and nothing else. Everything the platform must be able to say
    # later is a durable row: the gate is the cache, the evidence is the row.
    #
    # A **server-to-server** address, like `PHOTO_STORAGE_ENDPOINT_URL` and
    # `PHOTO_REVIEW_ENDPOINT_URL`, so the public-network scheme rule has nothing to
    # say about it — no browser and no phone ever opens it. A deployed environment
    # that wants TLS spells it `rediss://` in the URL it sets, which is the same
    # place it sets the credentials.
    #
    # **What is emphatically not here is either TTL.** How long a suppression lasts
    # is `PASS_SUPPRESS`, a product decision in the released ruleset; how long a
    # week of exposure survives is `EXPOSURE_RETENTION_WEEKS`, in
    # `matchmaking/domain/ledgers.py`. Both decide what can still be asked, and an
    # environment that could shorten either would be an environment selecting
    # behaviour a domain test can observe. What lives here is where the store is,
    # and how often the roll runs.
    REDIS_URL: str = DEFAULT_REDIS_URL

    # --- the exposure roll (docs/adr/0092, matchmaking-engine.md §14.5)
    #
    # Hourly, matching §14.5. The scalar it publishes is a percentile over a week's
    # appearances, which barely moves within an hour and is read on every search —
    # so the cadence is the trade between a stale threshold and an unbounded read on
    # the request path. Turning it off changes no rule a domain test could observe:
    # the *shown more than most* rung simply never fires, and the two rungs that
    # lift are unaffected, which is the state the platform is in today.
    EXPOSURE_ROLL_ENABLED: bool = True
    EXPOSURE_ROLL_INTERVAL_SECONDS: float = 60 * 60

    # --- the two prompt loops
    # (docs/adr/0092, docs/adr/0099, matchmaking-engine.md §6.3)
    #
    # **Each raises a question and changes no value**, which is what makes both
    # of them safe to turn off: the platform simply stops asking. Nothing a
    # domain test can observe moves — a search still runs on the same grid at the
    # same radius against the same floor, and the two per-search prompts, which
    # are facts about the search in front of you rather than about a history, are
    # raised on the request path and are not switchable at all.
    #
    # **What is emphatically not here is any of the four thresholds.** How many
    # searches make a drift, how many takes make a habit, how old a grid has to
    # be and how long a raised prompt lives are rules a domain test can observe,
    # and they live in `matchmaking/domain/prompts.py`. An environment that could
    # move one would be an environment deciding when a player gets asked about
    # their own profile — which is the same class of error as an environment that
    # could move the quality floor.
    #
    # Daily, matching §14.5's own cadence for the drift detector. Both read a
    # window wider than their interval, so a missed tick or a deploy does not
    # create a day nobody's drift was noticed in.
    INTENT_DRIFT_ENABLED: bool = True
    INTENT_DRIFT_INTERVAL_SECONDS: float = 24 * 60 * 60
    GRID_STALENESS_ENABLED: bool = True
    GRID_STALENESS_INTERVAL_SECONDS: float = 24 * 60 * 60

    # --- the interest expiry loop (docs/adr/0092, docs/adr/0127)
    #
    # **Turning it off changes no rule a domain test could observe.** Every read
    # of the interest ledger is bounded by `now`, so a yes stops lifting, stops
    # counting against the cap and stops being listed the moment it expires,
    # swept or not. What the loop buys is that the table stays the size of what
    # is live, and the one figure a lapsed row could ever be asked for — *yeses
    # that expired having never lifted anybody*, which is `INTEREST_TTL`'s only
    # day-one falsifier and cannot be computed after the rows are gone.
    #
    # **`INTEREST_TTL` itself is emphatically not here.** How long a yes lives
    # decides who is admitted below the quality floor, which is a rule a domain
    # test observes; it is a ruleset row, and only this cadence is a setting.
    #
    # Hourly, which is far finer than a twenty-one-day window needs and is chosen
    # against the other end: the sweep is a keyed delete over an indexed date, so
    # a frequent tick is cheap and a rare one lets a deploy gap turn into a
    # visibly growing table.
    INTEREST_EXPIRY_ENABLED: bool = True
    INTEREST_EXPIRY_INTERVAL_SECONDS: float = 60 * 60

    # --- the challenge lapse loop (docs/adr/0092)
    #
    # **Turning it off changes no rule a domain test could observe.** A seat past
    # its answer window reads as lapsed at every instant, its pair releases and
    # its challenge stands as `LAPSED` whether or not anything has swept it —
    # `standing.py` folds the seats against the clock and stores nothing. What
    # the loop buys is the *record*: a `SeatLapsed` in the log, so that **answers
    # challenges** has a denominator, and a lapse is a fact somebody can count
    # rather than an absence they have to infer.
    #
    # **`ANSWER_WINDOW` itself is emphatically not here.** How long an invitee has
    # to answer is the promise the invitation makes — behaviour a domain test can
    # observe, and an environment that could select it would be an environment
    # that decides how long a player has to answer — and it lives in
    # `challenges/domain/answer_window.py`. Only this cadence is a setting.
    # Moving it there moves nothing already sent: a seat's `answer_by` is stamped
    # when the seat is invited, so every outstanding challenge keeps the promise
    # it was sent with.
    #
    # Hourly, and the number it is chosen against is the window rather than the
    # backlog: a `SeatLapsed` is stamped with the moment the sweep noticed, so
    # the interval is how late the record is, and an hour against a two-day
    # window is a forty-eighth. Finer would buy a rounder timestamp and pay for
    # it in a read that is not yet indexed.
    CHALLENGE_LAPSE_ENABLED: bool = True
    CHALLENGE_LAPSE_INTERVAL_SECONDS: float = 60 * 60

    # --- the rating catch-up (docs/adr/0139)
    #
    # **The second job that appends a domain event, and the first whose absence a
    # player would notice.** A confirmation is a clock passing and nothing
    # announces one, so this is what turns a result into a Level that moved. Turn
    # it off and every rating on the platform quietly stops being tested — which
    # is why it is the one loop here whose default is on for a reason about the
    # product rather than about a record.
    #
    # Hourly, and the number is chosen against the clock the result settled on: a
    # move is stamped with the moment the result became final rather than with
    # the moment the run noticed, so the interval is how late the *stream* is and
    # never what it says. Finer would buy a fresher card and pay for it in a walk
    # of every game the platform has recorded.
    #
    # The **rule** it applies is not here and could not be: an environment that
    # could pick a K-factor is an environment that decides how a marketplace
    # rates people.
    RATING_CATCH_UP_ENABLED: bool = True
    RATING_CATCH_UP_INTERVAL_SECONDS: float = 60 * 60

    # --- the two scale triggers (docs/adr/0092, scale-posture.md §4)
    #
    # **The instruments are configuration; the thresholds are not.** How often
    # the loop-lag probe ticks and how many workers this container runs are
    # facts about the deployment. *p99 above 20 ms*, *duty cycle above 0.25* and
    # *half the container memory* are the numbers the escalation ladder is
    # climbed on, and they live in `matchmaking/domain/scale_triggers.py` — an
    # environment that could widen a trigger is an environment that decides when
    # the platform is in trouble.
    #
    # Turning the probe off changes nothing a domain test could observe: no
    # search is timed differently and no answer moves. What stops is the record,
    # and *a trigger that requires somebody to go and measure fires late* is the
    # reason the default is on.
    #
    # A second a tick, because the reading is the loop's own oversleep and a
    # probe that slept a minute would report a minute's worth of contention as
    # one sample. Fifteen minutes of ticks then close a window — the interval
    # that §4 states the trigger over, which is `TRIGGER_WINDOW` and not a
    # setting.
    SCALE_PRESSURE_ENABLED: bool = True
    SCALE_PRESSURE_INTERVAL_SECONDS: float = 1.0

    #: How many workers this container runs, read from the variable
    #: `docker/api/startup.prod.sh` already passes to gunicorn — so trigger 4's
    #: arithmetic reads the fleet that exists rather than one somebody typed
    #: twice. It selects no behaviour: it is a multiplier inside a log record.
    GUNICORN_WORKERS: int = 1

    @field_validator("APP_ENV", mode="before")
    @classmethod
    def _known_environment(cls, v):
        # Raised here rather than left to pydantic's own enum error, because that error
        # echoes the offending value back in `input_value=…`.
        if isinstance(v, Environment):
            return v
        try:
            return Environment(v)
        except ValueError:
            raise ConfigurationError(
                f"APP_ENV is not a known environment. It must be one of: "
                f"{ENVIRONMENT_NAMES}."
            ) from None

    @field_validator("ALLOW_ORIGINS", "ALLOW_METHODS", "ALLOW_HEADERS", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @field_validator("READER_DB_URL", mode="before")
    @classmethod
    def _default_reader(cls, v):
        return None if v == "" else v

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    def model_post_init(self, __context: Any) -> None:
        # Snapshot first: assigning below adds names to `model_fields_set`, so every
        # "did somebody actually configure this?" question is answered against the same
        # picture regardless of the order the answers are used in.
        provided = set(self.model_fields_set)

        profile = ENVIRONMENT_PROFILES[self.APP_ENV]
        if "DEBUG" not in provided:
            self.DEBUG = profile.DEBUG
        if "LOG_LEVEL" not in provided:
            self.LOG_LEVEL = profile.LOG_LEVEL
        if "LOG_JSON" not in provided:
            self.LOG_JSON = profile.LOG_JSON

        if self.READER_DB_URL is None:
            self.READER_DB_URL = self.WRITER_DB_URL

        self._refuse_dangerous_configuration(provided)

    def _refuse_dangerous_configuration(self, provided: Set[str]) -> None:
        """Refuse to start rather than run misconfigured. Order is not significant —
        each refusal is triggered by a different variable, and a configuration that
        trips two is broken either way."""
        env = self.APP_ENV

        if env in UNPROVISIONED:
            # "Configured" means somebody set it. There is nothing to compare a host
            # against, because no domain is registered and no placeholder hostname is
            # written anywhere — which is the point: an unprovisioned environment is
            # honest about being unprovisioned rather than falling back to the local
            # defaults and pointing at a database that is not there.
            if "APP_HOST" not in provided:
                raise ConfigurationError(
                    f"APP_HOST is not set, and APP_ENV selects '{env}', which is "
                    f"defined but not provisioned. No host exists for it yet — set "
                    f"APP_HOST explicitly or use 'local'."
                )
            if "WRITER_DB_URL" not in provided:
                raise ConfigurationError(
                    f"WRITER_DB_URL is not set, and APP_ENV selects '{env}', which is "
                    f"defined but not provisioned. Falling back to the local default "
                    f"would point at a database that does not exist — set "
                    f"WRITER_DB_URL explicitly or use 'local'."
                )
            if "REDIS_URL" not in provided:
                # The same refusal as the database's, and for the same reason
                # rather than for a weaker one. The ledgers behind it fail soft, so
                # an unreachable Redis costs a search its spread and nothing more —
                # but *silently degraded for ever* is not a state an environment
                # should be able to boot into by inheriting a laptop's service
                # name. A ledger that never works looks exactly like a quiet week.
                raise ConfigurationError(
                    f"REDIS_URL is not set, and APP_ENV selects '{env}', which is "
                    f"defined but not provisioned. Falling back to the local default "
                    f"would point at an ephemeral store that does not exist, and the "
                    f"ledgers behind it would degrade silently — set REDIS_URL "
                    f"explicitly or use 'local'."
                )

        if env in DEPLOYED:
            # The backend's instance of the platform's **public-network scheme rule**: a
            # URL a browser reaches over the internet is `https://` in every deployed
            # environment. The backend calls nothing over HTTP, so `ALLOW_ORIGINS` is
            # the only such URL it holds — these are the origins a browser presents, and
            # an `http://` one in a deployed environment means the club console is being
            # served in the clear, which is a session cookie in the clear.
            #
            # #99 added this. Until then the rule was carried by the two clients and not
            # by the backend, so "the three apps agree" was false in the one direction
            # nobody was looking: a deployed backend would happily hand credentialed
            # CORS permission to a plaintext origin.
            #
            # The wildcard is skipped deliberately — it is not an origin, and it has its
            # own refusal below. `local` is exempt because `http://localhost:3000` is
            # what the club app actually serves on a laptop.
            insecure = [
                origin
                for origin in self.ALLOW_ORIGINS
                if origin != CORS_WILDCARD
                and not origin.lower().startswith("https://")
            ]
            if insecure:
                raise ConfigurationError(
                    f"ALLOW_ORIGINS contains {len(insecure)} origin(s) that are not "
                    f"https://, and APP_ENV selects '{env}', which is deployed. A "
                    f"browser origin reached over a public network must be https:// "
                    f"there — an http:// one transmits the session cookie in the clear."
                )

        if env is not Environment.PRODUCTION:
            return

        if self.JWT_SECRET_KEY == DEFAULT_JWT_SECRET_KEY:
            raise ConfigurationError(
                "JWT_SECRET_KEY is still the shipped default in production. It is "
                "public in this repository's history, so every token it signs is "
                "forgeable. Generate one with: openssl rand -hex 32."
            )

        if self.PHOTO_STORAGE_SECRET_KEY == DEFAULT_PHOTO_STORAGE_SECRET_KEY:
            raise ConfigurationError(
                "PHOTO_STORAGE_SECRET_KEY is still the shipped default in production. "
                "It is the local MinIO container's, published in this repository, so "
                "it grants read and write access to every photo the platform holds."
            )

        if self.DEBUG:
            raise ConfigurationError(
                "DEBUG is on in production. It serves verbose errors to callers; "
                "interactive API documentation is disabled in production regardless."
            )

        if "*" in self.ALLOW_ORIGINS and self.ALLOW_CREDENTIALS:
            raise ConfigurationError(
                "ALLOW_ORIGINS is a wildcard while ALLOW_CREDENTIALS is on, in "
                "production. Browsers reject that combination anyway, so it cannot be "
                "mistaken for working configuration. List the origins explicitly."
            )

        if self.DB_SSL_MODE.lower() not in ENCRYPTED_DB_SSL_MODES:
            raise ConfigurationError(
                "DB_SSL_MODE does not encrypt the database connection, in production. "
                "It must be one of: " + ", ".join(sorted(ENCRYPTED_DB_SSL_MODES)) + "."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
