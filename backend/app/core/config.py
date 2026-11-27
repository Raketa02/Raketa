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


class SmtpSecurity(StrEnum):
    """How the connection to the mail relay is protected (``docs/adr/0186`` §1).

    ``none`` is for the local mail catcher, and a deployed environment refuses
    it: a reset code sent in the clear is a reset code anybody on the path can
    use. ``starttls`` upgrades a plain connection; ``tls`` is encrypted from the
    first byte. Either verifies the relay's certificate.
    """

    NONE = "none"
    STARTTLS = "starttls"
    TLS = "tls"


class PushProvider(StrEnum):
    """Which push service a notice is pushed through (#549; the mechanics
    §17.2).

    ``expo`` is Expo's push service, which reaches a phone running the app on
    Android and — with the Apple Developer membership publishing needs anyway —
    on iPhone. ``recording`` pushes nothing and remembers what it was asked: a
    laptop with no phone to push to may choose it, and a deployed environment
    refuses it, since every notice would reach nobody's phone.
    """

    EXPO = "expo"
    RECORDING = "recording"


class PaymentsProvider(StrEnum):
    """Which adapter money moves through (``docs/adr/0189`` §4).

    ``fake`` is the in-process provider a laptop, a seed run and every test use,
    and a deployed environment refuses it: it saves cards that do not exist and
    charges nobody, so a game would be booked that no one paid for. ``stripe`` is
    Stripe, in test mode or live according to the key it is given.
    """

    FAKE = "fake"
    STRIPE = "stripe"


#: The prefixes of a Stripe key that moves real money — a secret key and a
#: restricted one — and of one that moves only test money.
STRIPE_LIVE_KEY_PREFIXES = ("sk_live_", "rk_live_")
STRIPE_TEST_KEY_PREFIXES = ("sk_test_", "rk_test_")


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
DEFAULT_PHOTO_STORAGE_ACCESS_KEY = "rakieta_photos"
DEFAULT_PHOTO_STORAGE_SECRET_KEY = "rakieta_photos_pwd"

#: The shipped ephemeral-store address. `redis` is the service name in
#: `docker-compose-local.yml`, so this default resolves on a laptop running the dev
#: stack and resolves nowhere else — which is what makes it safe to refuse rather
#: than fall back on, exactly as the writer database's default is.
DEFAULT_REDIS_URL = "redis://redis:6379/0"

#: Where the public site answers on a laptop: ``frontend_public``'s dev server,
#: beside the club website's on 3000. It resolves on a developer's own machine and
#: nowhere else, which is what makes it safe to refuse rather than fall back on in
#: a deployed environment, exactly as the database's and Redis's defaults are.
DEFAULT_PUBLIC_SITE_URL = "http://localhost:3001"

#: Where the club website answers on a laptop: ``frontend_club``'s dev server
#: (``docs/adr/0187`` §7). A club's *Forgot password?* email links to its own
#: *Set a new password* page there, and a deployed environment refuses to
#: inherit it, exactly as it refuses the public site's.
DEFAULT_CLUB_WEBSITE_URL = "http://localhost:3000"

#: The mail catcher in ``docker-compose-local.yml`` — Mailpit's SMTP port, whose
#: web inbox is ``localhost:8025``. A service name, so it resolves on a laptop
#: running the dev stack and nowhere else, which is what makes it safe to refuse
#: rather than fall back on (``docs/adr/0186`` §1).
DEFAULT_SMTP_HOST = "mailpit"
DEFAULT_SMTP_PORT = 1025

#: Who a local email is from. The reserved ``.example`` domain, because no domain
#: is registered and a deployed environment must name a real sender.
DEFAULT_MAIL_SENDER = "Rakieta <no-reply@rakieta.example>"

#: The work factor every stored password and refresh token is hashed at in production,
#: and the floor for everything deployed. bcrypt's own default, so a deployed
#: environment that says nothing about it hashes exactly as it did before the setting
#: existed.
PRODUCTION_BCRYPT_ROUNDS = 12

#: The environments that run somewhere other than a developer's machine. `local` is not
#: one of them, which is what makes `http://localhost:3000` a legal allowed origin and
#: `redis://redis:6379/0` a working address.
#:
#: It answers two questions, and used to answer only the first: which environments a
#: browser reaches over a public network, and which ones may not inherit an address out
#: of `docker-compose-local.yml`. The second was once asked of `development` and
#: `staging` alone, under the name `UNPROVISIONED` — see the refusals below for why
#: that was the wrong half of the set (#341).
DEPLOYED = frozenset(
    {Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION}
)

#: The CORS wildcard. Not an origin, so the scheme rule below has nothing to say about
#: it — it is governed by its own refusal, in combination with `ALLOW_CREDENTIALS`.
CORS_WILDCARD = "*"


class Settings(BaseSettings):
    # --- app metadata
    TITLE: str = "Rakieta API"
    DESCRIPTION: str = "Production-ready Rakieta backend with auth"
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
        "postgresql+asyncpg://rakieta_user:rakieta_pwd@db:5432/rakieta"
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
    JWT_ISSUER: str = "rakieta"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 900
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400

    # --- password hashing
    #
    # bcrypt's cost, in bcrypt's own word for it: each step doubles the time one hash
    # takes. Production's in every environment unless somebody lowers it, and only a
    # laptop may — the test suite sets bcrypt's minimum, because at production's
    # strength every sign-up, login and refresh it makes costs a fifth of a second.
    #
    # It selects nothing a domain test could observe. bcrypt writes the cost into
    # the hash and `checkpw` reads it back from there, so a hash stored at one
    # setting verifies at every other.
    BCRYPT_ROUNDS: int = PRODUCTION_BCRYPT_ROUNDS

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

    # --- the public site (docs/adr/0187 §7, docs/adr/0183 §4)
    #
    # **Every group link is built from this address**: `<PUBLIC_SITE_URL>/join/`
    # and the group's code. The address is configuration and the shape is not —
    # the code is the group's identity, and a link printed under one
    # environment's domain and pasted into another's is still recognised by the
    # `/join/<code>` inside it. A browser and a phone open it over a public
    # network, so the scheme rule below holds it to `https://` once deployed.
    #
    # **Changing it re-addresses every link the backend serves from then on**
    # and none of the ones already posted into WhatsApp, which keep the domain
    # they were printed with. That is why it is set once per environment and
    # why a deployed environment must say it rather than inherit a laptop's.
    PUBLIC_SITE_URL: str = DEFAULT_PUBLIC_SITE_URL

    # --- the club website (docs/adr/0187 §7, docs/adr/0184 §5)
    #
    # **A club's reset link is built from this address**: its *Forgot
    # password?* email opens `<CLUB_WEBSITE_URL>/reset/<token>`, the website's
    # own *Set a new password* page, because clubs already use that site. Held
    # to `https://` once deployed, as the public site's address is.
    CLUB_WEBSITE_URL: str = DEFAULT_CLUB_WEBSITE_URL

    # --- the player app's scheme (docs/adr/0187 §7, docs/adr/0186 §3)
    #
    # **Where a button that opens the app goes**: the invitation an existing
    # account is sent has no link to set a password through, only the app to
    # accept it in, and every money email's button opens the app as well; each
    # goes to `<APP_SCHEME>://`. One scheme at every environment, as the app
    # itself declares one (`frontend_player`'s `app.config.ts`), so there is
    # nothing here for a deployed environment to refuse; universal links arrive
    # with a domain and replace it there.
    APP_SCHEME: str = "rakieta"

    # --- email (docs/adr/0186)
    #
    # **Where mail goes and who it is from are configuration; what it says, and
    # how long the link in it works, are not.** The copy lives with its
    # templates and the lifetimes in `auth/domain/one_time_credential.py`.
    #
    # Locally every email lands in the mail catcher's inbox and none leaves the
    # machine. **The production sender stays off until a domain exists**: a
    # deployed environment that names no relay, no sender or an unencrypted
    # connection refuses to start, and never falls back to not sending.
    MAIL_SENDER: str = DEFAULT_MAIL_SENDER
    SMTP_HOST: str = DEFAULT_SMTP_HOST
    SMTP_PORT: int = DEFAULT_SMTP_PORT
    SMTP_SECURITY: SmtpSecurity = SmtpSecurity.NONE
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    #: The whole budget for one send, connection included.
    SMTP_TIMEOUT_SECONDS: float = 10.0
    #: The mail catcher's web inbox, as the laptop's browser reaches it — where
    #: the dev console's *Sent* pane links each email (#594). Read by nothing a
    #: deployed environment serves: the console is `local`'s alone.
    MAIL_CATCHER_URL: str = "http://localhost:8025"

    # --- photo storage (S3-compatible: MinIO locally, S3 deployed — docs/adr/0091)
    #
    # `PHOTO_STORAGE_ENDPOINT_URL` is a **server-to-server** URL and carries no scheme
    # rule; `PHOTO_STORAGE_PUBLIC_ENDPOINT_URL` is the one a player's phone opens a
    # presigned URL against, and falls back to the first when unset. Both are `None` in
    # a deployed environment, where botocore resolves AWS's own https endpoints — which
    # is the whole of the adapter swap.
    PHOTO_STORAGE_ENDPOINT_URL: Optional[str] = "http://minio:9000"
    PHOTO_STORAGE_PUBLIC_ENDPOINT_URL: Optional[str] = None
    PHOTO_STORAGE_BUCKET: str = "rakieta-player-photos"
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

    # --- payments (docs/adr/0189 §4; the mechanics Appendix A)
    #
    # **Which provider money moves through, and the keys it holds, are
    # configuration; what is charged, when and to whom is not.** A share, a
    # cut-off and the fee withheld on a refund are rules a domain test observes,
    # and live with the Club courts and the bookings.
    #
    # A laptop runs on the in-process fake, which needs no key and never leaves
    # the machine. Stripe needs its secret key and the publishable key a phone
    # opens its card fields with; the webhook secrets are what each endpoint
    # verifies every event with — the platform's (`STRIPE_WEBHOOK_SECRET`) and
    # the **Connected accounts** endpoint's, where a club's account and the
    # payments made on it notify (`STRIPE_CONNECT_WEBHOOK_SECRET`, #537): Stripe
    # signs each endpoint's with its own. `stripe listen` prints one for a
    # laptop. **The keys are a person's to place** (#533), in `.env`, never an
    # agent's.
    #
    # **A live key moves real money**, so only production may hold one, and
    # production may hold nothing else: a test key there would book games that
    # nobody paid for. Neither refusal ever prints the key.
    PAYMENTS_PROVIDER: PaymentsProvider = PaymentsProvider.FAKE
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_CONNECT_WEBHOOK_SECRET: Optional[str] = None
    #: The whole budget for one call to Stripe, connection included. A setup
    #: waits on it inline, and a player is watching a spinner.
    STRIPE_TIMEOUT_SECONDS: float = 20.0
    #: **Read by nothing but the payments demand suite**: a club account a person
    #: onboarded once in Stripe test mode, which the suite charges against.
    #: Onboarding is a walk through Stripe's hosted pages that the suite does not
    #: script, so without it the money half of the suite is skipped by name.
    STRIPE_TEST_CLUB_ACCOUNT: Optional[str] = None

    # --- push notifications (#549; the mechanics §17.2)
    #
    # Expo's push service needs no key: a phone's push token is what it pushes
    # to. **An access token is optional and worth placing deployed** — with
    # *enhanced push security* switched on for the Expo project, Expo refuses a
    # push without it, which makes a phone's token useless to anybody else. A
    # person places it (#533), never an agent. A push that cannot be made is
    # logged and given up — the notice is in the player's list whatever happens.
    PUSH_PROVIDER: PushProvider = PushProvider.EXPO
    EXPO_PUSH_URL: str = "https://exp.host/--/api/v2/push/send"
    EXPO_ACCESS_TOKEN: Optional[str] = None
    #: The whole budget for one request to Expo. Pushing runs in the outbox's
    #: delivery, so a slow service holds the queue behind it for this long.
    EXPO_PUSH_TIMEOUT_SECONDS: float = 10.0

    # --- domain event delivery
    EVENT_DELIVERY_WORKER_ENABLED: bool = True
    EVENT_DELIVERY_POLL_INTERVAL_SECONDS: float = 1.0
    EVENT_DELIVERY_BATCH_SIZE: int = 100

    # --- the mail worker (docs/adr/0186 §2)
    #
    # **Turning it off is not a way of not sending.** Every email a use case
    # writes waits in the mail queue with its link and code until this sends it
    # and purges them, so a worker that never runs is a table of live secrets
    # nobody receives. It is a toggle for a test run, as the outbox's is.
    #
    # Two seconds, because a person is waiting on the other side of a *Forgot
    # password?* and a longer tick is a longer stare at an inbox. Each tick
    # sends at most a batch, one message per transaction.
    MAIL_DELIVERY_ENABLED: bool = True
    MAIL_DELIVERY_INTERVAL_SECONDS: float = 2.0
    MAIL_DELIVERY_BATCH_SIZE: int = 20

    # --- the book-by sweep (#538, the mechanics §5.4)
    #
    # **It buys the record, not correctness.** A proposal past its book-by is
    # over at every instant, swept or not: a yes on it is refused, it is off
    # every live list and no yes on it counts against a cap, because every read
    # compares the book-by with the clock. What the sweep writes is the
    # `ProposalExpired` a poster will be told from, and a projection whose live
    # reads stay narrow as it grows.
    #
    # **The book-by itself is emphatically not here**: it is the club's release
    # time, derived from its release lead in `clubs/domain/rakieta_terms.py`, and
    # an environment that could move it would decide when a player's yes lapses.
    #
    # Every minute, chosen against the record's lag rather than a backlog: the
    # read is one indexed range of unrecorded endings.
    PROPOSAL_EXPIRY_ENABLED: bool = True
    PROPOSAL_EXPIRY_INTERVAL_SECONDS: float = 60

    # --- time to pay (#625, the mechanics §12.2, Q109)
    #
    # **Correctness depends on it**: a payer acting past their time already
    # runs it out first, but only this reopens the seat for everybody else and
    # lets the holds kept for it go. **The thirty minutes are emphatically not
    # here**: they are domain, `proposals/domain/limits.py`'s `TIME_TO_PAY`.
    # Every thirty seconds, because the window is minutes long and the others'
    # money is held on their cards meanwhile.
    TIME_TO_PAY_ENABLED: bool = True
    TIME_TO_PAY_INTERVAL_SECONDS: float = 30

    # --- a friends game's invitations (#751; docs/adr/0202 §5)
    #
    # Runs out every invitation whose time to answer ended, so its sender is
    # told *didn't answer*. Correctness does not depend on it: every read says
    # so off the clock. **The 24 hours are not here**: they are domain,
    # `bookings/domain/booking.py`'s `TIME_TO_ANSWER`. Every thirty seconds,
    # like the other seat jobs.
    INVITATIONS_ENABLED: bool = True
    INVITATIONS_INTERVAL_SECONDS: float = 30

    # --- a friends game's cover warning (#752; the friends mechanics §10.2)
    #
    # Warns a *Split* sender once, a day before the cut-off, what it will take
    # for the seats still without their own payment. Correctness does not
    # depend on it: the cut-off takes the covers whether or not it ran. **The
    # day is not here**: it is domain, `bookings/domain/booking.py`'s
    # `COVER_WARNING_BEFORE`. Every thirty seconds, like the other seat jobs.
    COVER_WARNING_ENABLED: bool = True
    COVER_WARNING_INTERVAL_SECONDS: float = 30

    # --- the cut-off (#544, the mechanics §12.3, §16.12)
    #
    # **Correctness depends on it**, as on time to pay: a booked game with a
    # seat open since before its cut-off reads *called off* at every read from
    # the cut-off on, but only this gives everybody still in their money back,
    # frees the court and tells the club. **The cut-off itself is emphatically
    # not here**: it is the club's free-cancellation setting, kept on each
    # booking as it stood when the game filled. Every thirty seconds, because
    # the money is owed from the cut-off on.
    CUT_OFF_ENABLED: bool = True
    CUT_OFF_INTERVAL_SECONDS: float = 30

    # --- the holding (#639, the mechanics §12.2, Q113)
    #
    # **Correctness depends on it**: a share the fill only checked — its hold
    # would not have lasted until the cut-off — is held nowhere until this
    # holds it again, and a refused one gives its player their time to fix the
    # card. **When is emphatically not here**: four days before the cut-off, and
    # the six hours a hold must outlast it by, are domain
    # (`payments/domain/seat_charge.py`). Every thirty seconds, like the cut-off.
    HOLDING_ENABLED: bool = True
    HOLDING_INTERVAL_SECONDS: float = 30

    # --- How did it go? (#663, the mechanics §15.2)
    #
    # When a Competitive booked game's hour ends, all four are asked for the
    # score — while they are still at the club. A clock passing announces
    # nothing, so a job looks for the hours that ended. **When, and for how
    # long after, is emphatically not here**: the hour's end and the half hour
    # it is still asked within are domain (`games/domain/windows.py`,
    # `notifications/domain/notices.py`). Every thirty seconds, like the other
    # seat jobs.
    HOW_DID_IT_GO_ENABLED: bool = True
    HOW_DID_IT_GO_INTERVAL_SECONDS: float = 30

    # --- Get your level (#727, the mechanics §17.2, Q126)
    #
    # A day after an account's first group join, still rated in nothing, it is
    # told once, ever: *Get your level so your groups can deal you games.* A
    # day passing announces nothing, so a job looks for the accounts due.
    # **When, and for how long after, is emphatically not here**: the day and
    # the week it is still told within are domain
    # (`notifications/domain/notices.py`). Every five minutes: a nudge a day
    # after a join is not news by the second.
    GET_YOUR_LEVEL_ENABLED: bool = True
    GET_YOUR_LEVEL_INTERVAL_SECONDS: float = 300

    # --- club payouts (#548, the mechanics §12.6, §16.11)
    #
    # **Correctness depends on it**: a club is paid after its games are played,
    # and nothing else releases its money to its bank. **When is emphatically
    # not here**: a club day's payout is released at the day's close, a game
    # once it is over and its money settled — domain, in
    # `payments/domain/club_payout.py`. Every five minutes, because a day closes
    # once and its payout may wait for a capture or a refund still on its way.
    CLUB_PAYOUTS_ENABLED: bool = True
    CLUB_PAYOUTS_INTERVAL_SECONDS: float = 300

    # --- the club's daily summary of new bookings (#548, the mechanics §16.12)
    #
    # Sent once a club day closes, for the bookings made since the close
    # before — the day is domain, in `bookings/domain/summary.py`; only how
    # often a closed day is looked for is a setting.
    NEW_BOOKINGS_SUMMARY_ENABLED: bool = True
    NEW_BOOKINGS_SUMMARY_INTERVAL_SECONDS: float = 300

    # --- the proposer (#540, the mechanics §5, §6.2–§6.3)
    #
    # **The engine that builds games, and correctness depends on it**: nothing
    # else deals a *Picked for you* card, hands a seat a no left to the next
    # best fits, or widens a pick at half In. Two loops over one use case: the
    # **sweep** walks every pool on this cadence, and the **short tick** walks
    # the pools a change delivered in this process made due (somebody joined,
    # set their week, a club changed what it sells, somebody swiped) — so a
    # change is dealt from in seconds, and the sweep is what guarantees it.
    #
    # **What is dealt is domain and emphatically not here**: the most even
    # four, the three next best fits, the three versions, the fourteen days and
    # the ten kilometres are `proposals/domain/`'s. Only how often is a setting.
    PROPOSER_ENABLED: bool = True
    PROPOSER_INTERVAL_SECONDS: float = 300
    PROPOSER_ON_CHANGES_INTERVAL_SECONDS: float = 5

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

    # --- the ephemeral store (docs/adr/0093)
    #
    # **Redis holds only what is allowed to be lossy** — since the searches went
    # (#579) that is a room's live channel and who is typing in it, and since
    # #770 each sport's kept General order, a copy the ranking projection can
    # always make again — and nothing else. Everything the platform must be able
    # to say later is a durable row.
    #
    # A **server-to-server** address, like `PHOTO_STORAGE_ENDPOINT_URL` and
    # `PHOTO_REVIEW_ENDPOINT_URL`, so the public-network scheme rule has nothing to
    # say about it — no browser and no phone ever opens it. A deployed environment
    # that wants TLS spells it `rediss://` in the URL it sets, which is the same
    # place it sets the credentials.
    REDIS_URL: str = DEFAULT_REDIS_URL

    # --- the rating catch-up (docs/adr/0139)
    #
    # **The second job that appends a domain event, and the first whose absence a
    # player would notice.** A result settled by a window closing — silence, or
    # two scores naming the same winner — is a clock passing and nothing
    # announces one, so this is what turns it into a Level that moved. Turn it
    # off and those ratings quietly stop being tested — which is why it is the
    # one loop here whose default is on for a reason about the product rather
    # than about a record. (*That's right* settles at once and moves its Levels
    # from the outbox, #654.)
    #
    # Every minute, because **Levels move within a minute of a result settling**
    # (docs/adr/0195 §5): the hourly cadence is retired. A move is stamped with
    # the moment the result became final rather than with the moment the run
    # noticed, so the interval is how late the *stream* is and never what it
    # says — and the price of a fresh Level is a walk of every game the platform
    # has recorded, sixty times an hour.
    #
    # The **rule** it applies is not here and could not be: an environment that
    # could pick a K-factor is an environment that decides how a marketplace
    # rates people.
    RATING_CATCH_UP_ENABLED: bool = True
    RATING_CATCH_UP_INTERVAL_SECONDS: float = 60

    # --- the conversation sweep (docs/adr/0153, docs/adr/0142)
    #
    # **Turning it off changes no rule a domain test could observe.** A room past
    # its end answers `conversation_not_found` on every route and is gone from
    # every list whether or not anything has swept it — the end is a fold over
    # the room's own stream and is stored nowhere. What the loop buys is that the
    # destruction is **real**: *destroyed, not delisted* means the entries stop
    # existing rather than stopping being answered with, which is the whole
    # difference between a room that is over and a record with no end.
    #
    # **`CONVERSATION_GRACE` itself is emphatically not here.** How long a room
    # outlives the game it was opened for is behaviour a domain test can observe
    # — and an environment that could select it would be an environment that
    # decides how long two people keep each other — so it lives in
    # `conversations/domain/lifetime.py` beside the derivation that reads it.
    # Only this cadence is a setting.
    #
    # Hourly, and the number is chosen against what being late costs: nothing a
    # player can see, because the reads are already right, so this is purely how
    # long a dead room's rows sit in the table. Finer would buy a tidier database
    # and pay for it in a walk that folds every live room's stream.
    CONVERSATION_SWEEP_ENABLED: bool = True
    CONVERSATION_SWEEP_INTERVAL_SECONDS: float = 60 * 60

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

        if env in DEPLOYED:
            # "Configured" means somebody set it. There is nothing to compare a host
            # against, because no domain is registered and no placeholder hostname is
            # written anywhere — which is the point: a deployed environment is honest
            # about what nobody told it rather than falling back to the local defaults
            # and pointing at a database that is not there.
            #
            # **Every deployed environment, and once only the unbuilt two** (#341).
            # These three were stated over `development` and `staging`, on the reading
            # that what makes an address dangerous is the environment being
            # unprovisioned. It is not. What makes it dangerous is that the default is
            # a service name out of `docker-compose-local.yml`, which resolves on a
            # laptop and nowhere else — and that was most true of the one environment
            # the narrower set exempted. The committed ECS task definition selected
            # `production`, supplied no `REDIS_URL`, and would have run against
            # `redis://redis:6379/0` for ever: the permanently-degraded boot that
            # `infrastructure/redis_client.py` says must not be reachable, reached
            # through the door left open here.
            if "APP_HOST" not in provided:
                raise ConfigurationError(
                    f"APP_HOST is not set, and APP_ENV selects '{env}', which is "
                    f"deployed. No host is registered for it — set APP_HOST "
                    f"explicitly or use 'local'."
                )
            if "WRITER_DB_URL" not in provided:
                raise ConfigurationError(
                    f"WRITER_DB_URL is not set, and APP_ENV selects '{env}', which is "
                    f"deployed. Falling back to the local default would point at a "
                    f"database that does not exist — set WRITER_DB_URL explicitly or "
                    f"use 'local'."
                )
            if "REDIS_URL" not in provided:
                # The same refusal as the database's, and for the same reason
                # rather than for a weaker one. What sits behind it fails soft, so
                # an unreachable Redis costs a room its liveness and nothing more —
                # but *silently degraded for ever* is not a state an environment
                # should be able to boot into by inheriting a laptop's service
                # name. A live channel that never works looks like a quiet room.
                raise ConfigurationError(
                    f"REDIS_URL is not set, and APP_ENV selects '{env}', which is "
                    f"deployed. Falling back to the local default would point at an "
                    f"ephemeral store that does not exist, and the live channel "
                    f"behind it would degrade silently — set REDIS_URL explicitly or "
                    f"use 'local'."
                )
            if "PUBLIC_SITE_URL" not in provided:
                # The fourth of the same refusal, and the one whose damage
                # outlives the fix: every group link served while it is wrong
                # is posted into a WhatsApp chat and stays there, pointing at a
                # laptop's dev server, after the setting is corrected.
                raise ConfigurationError(
                    f"PUBLIC_SITE_URL is not set, and APP_ENV selects '{env}', "
                    f"which is deployed. Falling back to the local default would "
                    f"print every group link at a laptop's address — set "
                    f"PUBLIC_SITE_URL explicitly or use 'local'."
                )
            if "CLUB_WEBSITE_URL" not in provided:
                # The public site's refusal, for the other site the backend
                # prints links to: a club's reset email would open a laptop.
                raise ConfigurationError(
                    f"CLUB_WEBSITE_URL is not set, and APP_ENV selects '{env}', "
                    f"which is deployed. Falling back to the local default would "
                    f"send every club's reset link to a laptop's address — set "
                    f"CLUB_WEBSITE_URL explicitly or use 'local'."
                )
            if "SMTP_HOST" not in provided:
                # The same refusal as Redis's, and a stronger one: the default is
                # the local mail catcher's service name, so an environment that
                # inherited it would queue every reset and invitation for a
                # relay that does not exist. **This is where the production
                # sender stays off until a domain exists** — by refusing to
                # start, never by quietly not sending (``docs/adr/0186`` §1).
                raise ConfigurationError(
                    f"SMTP_HOST is not set, and APP_ENV selects '{env}', which is "
                    f"deployed. Falling back to the local mail catcher would leave "
                    f"every email undelivered — set SMTP_HOST to a relay or use "
                    f"'local'."
                )
            if "MAIL_SENDER" not in provided:
                raise ConfigurationError(
                    f"MAIL_SENDER is not set, and APP_ENV selects '{env}', which "
                    f"is deployed. The default sender is on a reserved domain no "
                    f"relay will send from — set MAIL_SENDER explicitly or use "
                    f"'local'."
                )
            if self.PAYMENTS_PROVIDER is PaymentsProvider.FAKE:
                # The same refusal again, and the one whose failure is money:
                # the fake saves cards that do not exist and charges nobody, so
                # every game it booked would be one no player paid for.
                raise ConfigurationError(
                    f"PAYMENTS_PROVIDER is the in-process fake, and APP_ENV "
                    f"selects '{env}', which is deployed. The fake charges nobody "
                    f"— set PAYMENTS_PROVIDER to stripe or use 'local'."
                )
            if self.PUSH_PROVIDER is PushProvider.RECORDING:
                # A notice would be given and pushed to nobody's phone.
                raise ConfigurationError(
                    f"PUSH_PROVIDER is the recording one, and APP_ENV selects "
                    f"'{env}', which is deployed. It pushes nothing — set "
                    f"PUSH_PROVIDER to expo or use 'local'."
                )

        if env in DEPLOYED:
            # A second question of the same set, kept separate because it is a rule
            # about *values* rather than about what nobody supplied.
            #
            # The backend's instance of the platform's **public-network scheme rule**: a
            # URL a browser reaches over the internet is `https://` in every deployed
            # environment. The backend calls nothing over HTTP, so it holds two such
            # URLs: `ALLOW_ORIGINS` — the origins a browser presents, where an
            # `http://` one in a deployed environment means the club console is being
            # served in the clear, which is a session cookie in the clear — and
            # `PUBLIC_SITE_URL`, which every group link is printed under (#504).
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
            # The second URL the backend holds that crosses a public network:
            # the address every group link is printed under, opened by whoever
            # taps one in a chat.
            if not self.PUBLIC_SITE_URL.lower().startswith("https://"):
                raise ConfigurationError(
                    f"PUBLIC_SITE_URL is not https://, and APP_ENV selects '{env}', "
                    f"which is deployed. Every group link is built from it and "
                    f"opened over a public network, so it must be https:// there."
                )
            if not self.CLUB_WEBSITE_URL.lower().startswith("https://"):
                raise ConfigurationError(
                    f"CLUB_WEBSITE_URL is not https://, and APP_ENV selects "
                    f"'{env}', which is deployed. A club's reset link is built "
                    f"from it and opened over a public network, so it must be "
                    f"https:// there."
                )
            # The scheme rule's mail-shaped instance: every email with a link
            # and a code crosses a public network to the relay, and a code sent
            # in the clear is a code anybody on the path can use.
            if self.SMTP_SECURITY is SmtpSecurity.NONE:
                raise ConfigurationError(
                    f"SMTP_SECURITY is 'none', and APP_ENV selects '{env}', which "
                    f"is deployed. Every reset and invitation email carries a code "
                    f"that opens an account, so the connection to the relay must "
                    f"be encrypted there — set SMTP_SECURITY to starttls or tls."
                )

        if env in DEPLOYED:
            # A third question of the same set, and the one about what is stored
            # rather than what is reached.
            #
            # Stated over every deployed environment rather than production alone,
            # because a staging database holds real people's passwords as soon as
            # anybody signs up to rehearse against it. Nothing fails at a weak cost —
            # every login still works — so the only thing that would ever notice is
            # somebody cracking the table.
            #
            # The message names no number, not even the floor: a refusal never
            # contains the offending value, and "12" contains a 1 and a 2.
            if self.BCRYPT_ROUNDS < PRODUCTION_BCRYPT_ROUNDS:
                raise ConfigurationError(
                    f"BCRYPT_ROUNDS is below production's work factor, and APP_ENV "
                    f"selects '{env}', which is deployed. A weaker hash is for a test "
                    f"run on a laptop — unset BCRYPT_ROUNDS to hash at production's "
                    f"strength."
                )

        if self.PAYMENTS_PROVIDER is PaymentsProvider.STRIPE:
            # Stripe cannot be asked anything without its secret key, and a
            # phone cannot open its card fields without the publishable one.
            # The webhook secrets are optional only on a laptop, whose
            # endpoints then answer every event with 503 — anything deployed
            # must verify what it is sent, at both endpoints: a club whose
            # account notices were never read would never go live.
            required = ["STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY"]
            if env in DEPLOYED:
                required.extend(
                    ["STRIPE_WEBHOOK_SECRET", "STRIPE_CONNECT_WEBHOOK_SECRET"]
                )
            for name in required:
                if not getattr(self, name):
                    raise ConfigurationError(
                        f"{name} is not set, and PAYMENTS_PROVIDER selects "
                        f"stripe. Place the key from the Stripe dashboard in "
                        f"the environment, or select the fake on a laptop."
                    )

        key = self.STRIPE_SECRET_KEY or ""
        if env is not Environment.PRODUCTION and key.startswith(
            STRIPE_LIVE_KEY_PREFIXES
        ):
            # Whichever provider is selected: a live key on a laptop is a key
            # one setting away from charging real cards from a test run.
            raise ConfigurationError(
                f"STRIPE_SECRET_KEY is a live key, and APP_ENV selects '{env}'. "
                f"A live key moves real money and only production may hold one "
                f"— use a test key (sk_test_…) here."
            )

        if env is not Environment.PRODUCTION:
            return

        if key.startswith(STRIPE_TEST_KEY_PREFIXES):
            raise ConfigurationError(
                "STRIPE_SECRET_KEY is a test key in production. Every game it "
                "booked would be one nobody paid for — use the live key."
            )

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
