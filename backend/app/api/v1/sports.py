"""The Sport registry, served read-only over the player API.

The registry is a closed set in the shared kernel; this route exposes it so that
neither client hardcodes the sports, their player counts or their durations. A
change to the registry ships without an app-store release.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.kernel import SPORT_SPECS, Sport, SportSpec

router = APIRouter(prefix="/sports", tags=["sports"])


class SportResource(BaseModel):
    """One sport as served: how many play it and the durations it is sold in."""

    sport: Sport
    players: int = Field(..., description="Number of players the sport is played for")
    durations: list[int] = Field(
        ..., description="Bookable durations in minutes, ascending"
    )

    @classmethod
    def from_spec(cls, spec: SportSpec) -> "SportResource":
        return cls(
            sport=spec.sport,
            players=spec.players,
            durations=list(spec.durations),
        )


class SportsResponse(BaseModel):
    sports: list[SportResource]


@router.get(
    "",
    response_model=SportsResponse,
    status_code=status.HTTP_200_OK,
    summary="List the supported sports",
)
async def list_sports() -> SportsResponse:
    return SportsResponse(
        sports=[SportResource.from_spec(SPORT_SPECS[sport]) for sport in Sport]
    )
