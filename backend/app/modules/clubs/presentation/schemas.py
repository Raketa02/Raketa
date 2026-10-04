"""The club surface's shapes for a club and its details.

**The requests declare types and nothing else**, and that is deliberate. Every
content rule — a name's length, an empty sports list, a point off the globe, a
weak password — is the value objects', and is refused with a code and
``details.field`` (``clubs/domain/errors.py``), because the club website writes
its sentence under the field it names. A bound restated here would refuse the
same input first, as a ``422 validation_error`` that names no field a client may
read. What stays here is what no person types: the sports are the registry's
codes, and anything else is refused before it is read.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.kernel import Sport
from app.modules.clubs.application.commands import ClubDetailsInput
from app.modules.clubs.domain.club import Club


class MapPointSchema(BaseModel):
    """Where the club is: the pin as the desk dropped it, never rounded."""

    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(description="Decimal degrees, within ±90.")
    longitude: float = Field(description="Decimal degrees, within ±180.")


class ClubDetailsRequest(BaseModel):
    """The five details, **all of them on every save** — the club website edits
    them on one page, and a save is a full replacement."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "Trimmed, runs of whitespace collapsed, then 2–80 characters. Never "
            "unique. Refused with `club_name_invalid`."
        )
    )
    district: str = Field(
        description="As the desk writes it, 2–64 characters. `club_district_invalid`."
    )
    city: str = Field(description="2–64 characters. `club_city_invalid`.")
    sports: list[Sport] = Field(
        description=(
            "The sports the club offers — at least one, `club_sports_required` "
            "otherwise. A sport ticked twice is ticked once, and the answer lists "
            "them in the registry's order."
        )
    )
    point: MapPointSchema = Field(
        description="The map pin. Off the globe is `club_point_invalid`."
    )

    def to_input(self) -> ClubDetailsInput:
        return ClubDetailsInput(
            name=self.name,
            district=self.district,
            city=self.city,
            sports=tuple(self.sports),
            latitude=self.point.latitude,
            longitude=self.point.longitude,
        )


class ClubSignUpRequest(ClubDetailsRequest):
    """A club signs up: its details, and the email and password its desk signs
    in with. **No second password field** — the website asks once."""

    email: str = Field(
        description=(
            "Unique among club accounts, and may also belong to an unrelated "
            "player. Malformed is `email_invalid`; another club's is `409 "
            "club_email_already_registered`."
        )
    )
    password: str = Field(
        description=(
            "8–128 characters with a letter and a digit — the player's rule. "
            "`password_too_weak` otherwise."
        )
    )


class ClubDetailsResponse(BaseModel):
    """A club as the desk sees it."""

    id: UUID
    name: str
    district: str
    city: str
    sports: list[Sport] = Field(description="In the registry's order.")
    point: MapPointSchema

    @classmethod
    def from_domain(cls, club: Club) -> "ClubDetailsResponse":
        details = club.details
        return cls(
            id=club.id,
            name=details.name.value,
            district=details.district.value,
            city=details.city.value,
            sports=list(details.sports.in_registry_order()),
            point=MapPointSchema(
                latitude=details.point.latitude, longitude=details.point.longitude
            ),
        )
