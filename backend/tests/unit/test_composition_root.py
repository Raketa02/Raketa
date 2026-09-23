"""The composition root is one root, and it does not need a request.

Three claims, and each one fails differently:

1. **Every port a use case depends on is constructible from a session and the
   settings** — asserted by building them all and then *running* two real use
   cases through the result. A factory that returns an object nobody exercises
   proves only that a constructor accepts its arguments.
2. **The domain-event runtime is reachable without reading state off a request**,
   and the application's own state holds that same runtime rather than a second
   one built beside it.
3. **The framework's dependency declarations construct no adapter** — a
   structural walk, because the failure mode is one line of convenience inside a
   `Depends` callable and nothing about a green suite would look different
   afterwards. That line is how a second composition root starts.

**What is deliberately not asserted, and why:** that importing the factories
pulls in no web framework at all. It does today — `app.modules.rating.domain.
errors` takes its base classes from `app.core.exception_handlers`, which imports
FastAPI, so every domain layer transitively depends on it (#101). That is
pre-existing, unrelated to configuration or composition, and not this module's
to fix; asserting it here would be asserting somebody else's bug is absent. What
*is* asserted is the part this module controls and the part that would regress
first: no direct import of a web framework in the factories themselves.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from app.bootstrap.composition import (
    build_assessment_engine,
    build_assessment_repository,
    build_block_query,
    build_block_repository,
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_image_transcoder,
    build_password_hasher,
    build_photo_review,
    build_photo_storage,
    build_play_intent_declaration_repository,
    build_player_profile_repository,
    build_refresh_token_repository,
    build_skill_rating_repository,
    build_token_service,
    build_unit_of_work,
    build_user_repository,
)
from app.bootstrap.events import EventRuntime, build_event_runtime, get_event_runtime
from app.core.config import get_settings
from app.kernel import Sport
from app.main import create_app
from app.modules.player_profile.application.commands import UploadPhotoCommand
from app.modules.player_profile.application.upload_photo import UploadPhoto
from app.modules.player_profile.domain.errors import UnsupportedImageFormat
from app.modules.rating.application.commands import CreateAssessmentCommand
from app.modules.rating.application.create_assessment import CreateAssessment
from app.modules.users.application.commands import RegisterUserCommand
from app.modules.users.application.register_user import RegisterUser
from app.shared.ids import new_uuid

ROOT = Path(__file__).resolve().parents[2]

#: The infrastructure imports a dependency declaration may keep. Neither is an
#: adapter: one is the request-scoped session itself, the other the process's
#: Redis connection pool. They are the connections everything else is built
#: *over*, and a declaration naming one is saying when it is handed out, not
#: choosing an implementation.
#:
#: A closed set rather than a prefix, so that the next thing under
#: `app.infrastructure.` has to be argued onto this list instead of inheriting
#: the allowance.
CONNECTION_PROVIDERS = frozenset(
    {
        "app.infrastructure.database.session",
        "app.infrastructure.redis_client",
    }
)

_MODULE_ADAPTER = re.compile(r"^app\.modules\.[^.]+\.infrastructure(\.|$)")
_ENGINE_VERSION = re.compile(r"^app\.engines\.[^.]+\.v\d+(\.|$)")


def declaration_modules() -> list[Path]:
    """Every file that declares dependencies to the web framework.

    A glob rather than a written-out list, so a context created tomorrow is
    covered on the day it exists. That convenience has the cost the
    configuration fence's wildcards have — a glob matching nothing passes
    silently — so the count is asserted below rather than trusted.
    """

    found = [ROOT / "app" / "api" / "dependencies.py"]
    found += sorted((ROOT / "app" / "modules").glob("*/presentation/dependencies.py"))
    return [path for path in found if path.exists()]


def imported_modules(path: Path) -> set[str]:
    """Absolute module paths this file imports, `from x import y` included."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
    return names


def is_adapter(module: str) -> bool:
    if module in CONNECTION_PROVIDERS:
        return False
    if module.startswith("app.infrastructure."):
        return True
    if _MODULE_ADAPTER.match(module):
        return True
    # A version package, not the abstraction beside it: importing
    # `app.engines.assessment` is naming a port, importing
    # `app.engines.racketskill.v3` is choosing an implementation.
    return bool(_ENGINE_VERSION.match(module))


# ---------------------------------------------------------------------------
# 1. Constructible from a session and the settings
# ---------------------------------------------------------------------------


async def test_every_port_is_built_from_a_session_and_the_settings(session_factory):
    """No application, no request, no `Depends` — a session and the settings.

    Written out one factory per line rather than looped over the module, because
    a factory this test does not name is a factory nothing proved constructible.
    """

    settings = get_settings()

    async with session_factory() as session:
        store = build_domain_event_store(session)
        events = build_event_publisher(session)

        built = [
            build_clock(),
            build_unit_of_work(session),
            store,
            events,
            build_password_hasher(settings),
            build_token_service(settings),
            build_refresh_token_repository(session),
            build_user_repository(session),
            build_assessment_engine(),
            build_assessment_repository(event_store=store, events=events),
            build_skill_rating_repository(event_store=store, events=events),
            build_player_profile_repository(event_store=store, events=events),
            # Declared before its first caller exists: the aggregate and its
            # durable contract landed with #182 so the candidate index has an
            # event to read, while ADR-0094's write path is its own build.
            build_play_intent_declaration_repository(event_store=store, events=events),
            # Also declared before their first caller: every surface that shows
            # one player to another consults `BlockQuery` (`docs/adr/0095` §7),
            # and none of those surfaces is built.
            build_block_repository(event_store=store, events=events),
            build_block_query(session),
            # No session: photos are bytes in an object store, not rows. What
            # they need instead is the settings — the bucket and which store —
            # which is the other half of what this module promises a caller
            # outside a request.
            build_photo_storage(settings),
            build_image_transcoder(),
            build_photo_review(settings),
        ]

    assert all(port is not None for port in built)


async def test_a_registration_runs_through_the_factories_alone(session_factory):
    """The tracer the seed system needs: a use case assembled from the factories
    writes an aggregate, and the write is visible on the way back out."""

    async with session_factory() as session:
        register = RegisterUser(
            users=build_user_repository(session),
            event_store=build_domain_event_store(session),
            hasher=build_password_hasher(get_settings()),
            uow=build_unit_of_work(session),
            clock=build_clock(),
            events=build_event_publisher(session),
        )

        user = await register.execute(
            RegisterUserCommand(
                email="composed@example.test",
                password="hunter22!",
                adult_attested=True,
            )
        )

        assert user.email.value == "composed@example.test"
        found = await build_user_repository(session).get_by_email(
            "composed@example.test"
        )
        assert found is not None


async def test_an_event_sourced_use_case_runs_through_the_factories_alone(
    session_factory,
):
    """The event-sourced half, which is the half that needs the runtime: the
    store, the publisher and the engine all resolve without an app, and the
    opening question comes back."""

    async with session_factory() as session:
        store = build_domain_event_store(session)
        events = build_event_publisher(session)
        create = CreateAssessment(
            engine=build_assessment_engine(),
            assessments=build_assessment_repository(event_store=store, events=events),
            ratings=build_skill_rating_repository(event_store=store, events=events),
            uow=build_unit_of_work(session),
            clock=build_clock(),
        )

        start = await create.execute(
            CreateAssessmentCommand(player_id=new_uuid(), sport=Sport.PADEL)
        )

    assert start.step.question is not None


# ---------------------------------------------------------------------------
# 2. The event runtime, without a request
# ---------------------------------------------------------------------------


def test_the_event_runtime_is_reachable_without_a_request():
    runtime = get_event_runtime()

    assert isinstance(runtime, EventRuntime)
    assert get_event_runtime() is runtime, "the process's runtime, built once"


def test_build_event_runtime_still_hands_back_a_fresh_one():
    """The cached accessor is the default, not the only door: a caller that
    genuinely wants an isolated catalog still has one."""

    assert build_event_runtime() is not get_event_runtime()


def test_the_application_state_holds_the_process_runtime():
    """One runtime, not two. The embedded delivery worker reads `app.state` and
    request handlers resolve the accessor; if those were different objects, a
    worker could dispatch through a different catalog than the requests that
    wrote the events — undetectable until an event went undelivered."""

    get_settings.cache_clear()
    app = create_app()

    assert app.state.event_runtime is get_event_runtime()


# ---------------------------------------------------------------------------
# 3. The declarations construct no adapter
# ---------------------------------------------------------------------------


def test_the_declaration_modules_were_actually_found():
    """The glob's preflight. A walk over nothing passes, which would make every
    assertion below decoration."""

    found = declaration_modules()

    assert len(found) >= 4, [str(p.relative_to(ROOT)) for p in found]


@pytest.mark.parametrize(
    "path", declaration_modules(), ids=lambda p: str(p.relative_to(ROOT))
)
def test_a_dependency_declaration_constructs_no_adapter(path: Path):
    """`Depends` callables declare *when* an adapter is built and how long it
    lives. What is built is `app.bootstrap.composition`'s answer, so that a seed
    run and a request get the same wiring rather than two copies of it."""

    offenders = sorted(m for m in imported_modules(path) if is_adapter(m))

    assert offenders == [], (
        f"{path.relative_to(ROOT)} imports an adapter: {offenders}. "
        "Adapters are constructed in app/bootstrap/composition.py; this file "
        "declares when they are built, not what."
    )


def test_the_factories_import_no_web_framework():
    """Directly, which is the part this module controls. The transitive claim is
    false today for a reason that is not composition's — see the module
    docstring and #101."""

    imported = imported_modules(ROOT / "app" / "bootstrap" / "composition.py")
    frameworks = sorted(
        m for m in imported if m.split(".")[0] in {"fastapi", "starlette"}
    )

    assert frameworks == []


async def test_the_photo_path_is_assembled_without_a_session_or_a_request():
    """The upload path runs on the settings alone — no database at all.

    Worth its own case rather than a line in the list above: every other port in
    this module takes a session, so *this* is the one that proves the factories
    are a function of configuration and not of a request that happens to carry a
    transaction. It is what a sweep job (#142) will need.
    """

    settings = get_settings()

    use_case = UploadPhoto(
        storage=build_photo_storage(settings),
        transcoder=build_image_transcoder(),
        review=build_photo_review(settings),
        clock=build_clock(),
        url_valid_for_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES,
    )

    # Executed as far as it can go without a store: the transcoder and the
    # reviewer are real, and a refused format proves the wiring runs rather than
    # only that the constructors accepted their arguments.
    with pytest.raises(UnsupportedImageFormat):
        await use_case.execute(
            UploadPhotoCommand(
                owner_id=new_uuid(),
                data=b"not an image",
                declared_media_type="image/gif",
            )
        )
