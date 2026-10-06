"""The envelope's invariants — the ones a new error class can silently break.

An error added six months from now that forgets its own ``code`` inherits its
base class's, and arrives on the wire indistinguishable from every other error
of that status. Nothing about that failure is visible in review: the class looks
fine, the status is right, and the message reads well. It shows up as a client
that cannot tell two recoveries apart. So it is asserted here rather than
watched for.
"""

from __future__ import annotations

import json
import re

import pytest

from app.api.contract import (
    _BACKEND_ROOT as BACKEND_ROOT,
    ERROR_SCHEMA_NAME,
    SURFACES,
    build_surface_spec,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.events.store import EventStreamVersionConflict
from app.core.exception_handlers import (
    CONCURRENT_MODIFICATION_CODE,
    code_for_status,
    register_exception_handlers,
)
from app.shared.domain.errors import (
    AppError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)

# Imported for their side effect: every error module must be loaded before the
# subclass walk below can see its classes.
from app.modules.auth.domain import errors as auth_errors  # noqa: F401
from app.modules.blocks.domain import errors as blocks_errors  # noqa: F401
from app.modules.clubs.domain import errors as clubs_errors  # noqa: F401
from app.modules.games.domain import errors as games_errors  # noqa: F401
from app.modules.matchmaking.domain import (  # noqa: F401
    errors as matchmaking_errors,
)
from app.modules.payments.domain import errors as payments_errors  # noqa: F401
from app.modules.player_profile.domain import errors as profile_errors
from app.modules.rating.domain import errors as rating_errors
from app.modules.users.domain import errors as users_errors  # noqa: F401

#: The generic ones. Each is a status's default and is allowed to be shared;
#: everything below them is a specific failure and must say which.
BASE_ERRORS = {
    AppError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
}

CODE_PATTERN = re.compile(r"\A[a-z][a-z0-9_]*\Z")


def _all_error_classes() -> list[type[AppError]]:
    found: list[type[AppError]] = []
    frontier = [AppError]
    while frontier:
        cls = frontier.pop()
        found.append(cls)
        frontier.extend(cls.__subclasses__())
    return found


def _domain_errors() -> list[type[AppError]]:
    return [cls for cls in _all_error_classes() if cls not in BASE_ERRORS]


def test_the_walk_actually_finds_the_domain_errors():
    # Guards the tests below: an import that stops happening would otherwise
    # make them pass by finding nothing.
    names = {cls.__name__ for cls in _domain_errors()}
    assert {
        "AssessmentNotFound",
        "QuestionNotOutstanding",
        "AssessmentAlreadyFinished",
        "InvalidAnswerOption",
        "InvalidCredentials",
        "EmailAlreadyRegistered",
        "AccessTokenExpired",
        "PhotoNotFound",
        "WeeklyHoursEmpty",
        "PlayerProfileAlreadyExists",
        "GateDataUnavailable",
        "TheCourtHasAnOpenSeat",
        "AccountHeld",
        "ClubEmailAlreadyRegistered",
    } <= names


@pytest.mark.parametrize(
    "error_class", _domain_errors(), ids=lambda cls: cls.__name__
)
def test_every_domain_error_declares_its_own_code(error_class):
    assert "code" in vars(error_class), (
        f"{error_class.__name__} inherits {error_class.code!r} from its base class, "
        "so it is indistinguishable on the wire from every other error of that status"
    )
    assert CODE_PATTERN.match(error_class.code)


def test_codes_are_unique_across_every_module():
    codes = [cls.code for cls in _domain_errors()]
    assert len(codes) == len(set(codes)), sorted(
        code for code in codes if codes.count(code) > 1
    )


def test_the_two_conflicting_assessment_errors_are_distinguishable():
    # The pair the client's recoveries are opposite for: refetch the current
    # step, versus jump to the result. Same status, same endpoint family.
    assert (
        rating_errors.QuestionNotOutstanding.code
        != rating_errors.AssessmentAlreadyFinished.code
    )
    assert (
        rating_errors.QuestionNotOutstanding().status_code
        == rating_errors.AssessmentAlreadyFinished().status_code
        == 409
    )


def test_the_profile_commits_refusals_are_distinguishable():
    """The 400s the commit can answer with arrive on the same status from the
    same endpoint and ask the client for different things: re-read the options,
    pick fewer tags, deduplicate the picker, tick an hour of the week, or
    rewrite the line. The radius and the opt-in had a refusal each until they
    went (#581)."""

    refusals = [
        profile_errors.UnknownSocialTag(),
        profile_errors.SocialTagSelectionOutOfBounds(),
        profile_errors.DuplicateSocialTag(),
        profile_errors.WeeklyHoursEmpty(),
        profile_errors.IntroNotAdmitted(profile_errors.IntroRefusal.TOO_LONG),
    ]

    assert len({error.code for error in refusals}) == len(refusals)
    assert {error.status_code for error in refusals} == {400}


def test_a_code_is_not_derived_from_the_message():
    # Rewording is a copy change, not a contract change. If a code were ever
    # computed from a message, this is the test that would notice.
    error = rating_errors.QuestionNotOutstanding()
    assert error.code == "question_not_outstanding"
    error.message = "Completely different wording."
    assert error.code == "question_not_outstanding"


def test_unauthored_statuses_still_get_a_code():
    assert code_for_status(404) == "not_found"
    assert code_for_status(422) == "validation_error"
    assert code_for_status(503) == "internal_error"
    assert code_for_status(418) == "request_failed"


# --- The envelope as published on both contract documents ----------------------


@pytest.mark.parametrize("surface", sorted(SURFACES))
def test_the_envelope_is_a_schema_on_every_surface(surface):
    # Both clients generate an error *type*, rather than treating a failure body
    # as untyped JSON — including a surface that has no paths yet.
    spec = build_surface_spec(surface, SURFACES[surface])
    schema = spec["components"]["schemas"][ERROR_SCHEMA_NAME]

    assert set(schema["properties"]) == {"code", "message", "trace_id", "details"}
    assert set(schema["required"]) == {"code", "message", "trace_id"}


@pytest.mark.parametrize("surface", sorted(SURFACES))
def test_the_committed_document_carries_the_envelope(surface):
    # `make openapi` writes these and the clients read them; a stale file is a
    # client generating types for a contract the server no longer serves.
    committed = json.loads(
        (BACKEND_ROOT / f"openapi.{surface}.json").read_text()
    )

    assert ERROR_SCHEMA_NAME in committed["components"]["schemas"]


# --- The conflict no context authored ------------------------------------------


def test_the_stream_conflict_code_collides_with_no_domain_error():
    # It is mapped centrally rather than re-declared per module, so it is not in
    # the subclass walk above and would not be caught by the uniqueness test.
    assert CODE_PATTERN.match(CONCURRENT_MODIFICATION_CODE)
    assert CONCURRENT_MODIFICATION_CODE not in {cls.code for cls in _domain_errors()}


def test_a_stream_version_conflict_is_a_409_in_the_envelope():
    # Until this handler existed, a genuine concurrent write told the client the
    # server had broken. It is a 409 for the same reason
    # `question_not_outstanding` is: the recovery is to re-read and retry.
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def _boom() -> None:
        raise EventStreamVersionConflict(
            "Expected assessment/00000000-0000-0000-0000-000000000001 at "
            "version 0, found 1"
        )

    response = TestClient(app, raise_server_exceptions=False).get("/boom")

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == CONCURRENT_MODIFICATION_CODE
    assert body["trace_id"]
    # The exception's own text names a stream and two versions. That is a fact
    # about our storage, and it stays in the log.
    assert "version" not in body["message"]
    assert "assessment/" not in body["message"]
