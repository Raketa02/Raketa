"""*Run it now*: a timed rule's job, run over what is due at the real *now*
(``docs/adr/0194`` §5; #591 builds the club's answer window, #592 the rest).

**It runs the job's own unit of work** — the code the scheduler's loop runs
each tick (``app/bootstrap/jobs.py``) — over this request's session and clock,
which is the real *now*. **It never brings anything forward**: a unit of work
acts only on what is already due, so a press does nothing the next scheduled
tick would not, and work that is not due yet is left exactly as it was.

A job's path is its name in the logs and on its task, so the press and the
scheduler are one job by one name.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dev.dependencies import ExpireUnansweredRequestsDep
from app.bootstrap.jobs import REQUEST_TIMEOUT_JOB

router = APIRouter(prefix="/jobs", tags=["dev"])


class RanResponse(BaseModel):
    job: str = Field(description="The job's name, as the scheduler runs it.")
    done: int = Field(description="What was due, and was done.")
    conflicts: int = Field(
        description="What another process was doing at that moment, stepped over."
    )
    says: str = Field(description="What happened, for the tester.")


@router.post(
    f"/{REQUEST_TIMEOUT_JOB}",
    response_model=RanResponse,
    summary="Run it now · the club's answer window",
    description=(
        "Calls off every request an On request club has not answered by its "
        "deadline — *Called off · no answer*, nobody paid, the court free and "
        "the players owed a new card. A request still inside its time to "
        "confirm is left waiting."
    ),
)
async def run_the_request_timeout(expire: ExpireUnansweredRequestsDep) -> RanResponse:
    unanswered = await expire.execute()
    return RanResponse(
        job=REQUEST_TIMEOUT_JOB,
        done=unanswered.requests,
        conflicts=unanswered.conflicts,
        says=(
            f"{unanswered.requests} request(s) past the club's answer called off."
            if unanswered.requests
            else "No request is past the club's answer yet: nothing was done."
        ),
    )
