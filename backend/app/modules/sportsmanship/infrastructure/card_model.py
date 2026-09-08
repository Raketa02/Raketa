"""The two sportsmanship tables. **The collapse is the primary key.**

``sportsmanship_card`` is one row per court a player has answered for, and
``sportsmanship_rating`` is one row per person they hold an opinion about. They
are two tables because *the card was answered* and *this is what I thought of
Ana* have different lifetimes and different keys, and because an all-blank card
has to be storable — it is a card row with nothing pointing at it.

**``sportsmanship_rating`` is keyed on the pair and not on the game**, which is
the whole of *only a rater's most recent rating of a given person counts*
(``docs/adr/0154``). Two friends who partner every week would otherwise supply
each other with ten of their twelve ratings, and the published average would drift
towards what one regular partner thinks — the opposite of what the row claims to
measure. Keyed this way a later card **replaces** the earlier answer, so the
collapse is a fact about the schema rather than a discipline every future reader
has to remember, and the count beside the figure keeps meaning *how many different
people have an opinion*. The earlier answer is not archived anywhere: individual
ratings reach nobody, there is no appeal route behind the figure, and a history
kept for nobody to read is a history somebody eventually reads.

**``game_id`` on the rating is which card the standing answer came from**, not a
key. It carries the composite foreign key back to the card, so a rating that came
from no answered card cannot exist.

**No blanks are stored.** Somebody left blank is absent from this table, which is
what makes *not rating produces no record of the omission* structural. It is also
why the card table cannot be derived from this one and has to exist.

**No event stream and no outbox.** A card is born answered, nothing amends it and
nothing subscribes to one being written — the published figure is a fold over
these rows at the moment somebody opens a record.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    SmallInteger,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class SportsmanshipCardORM(Base):
    """One player's answer to one court's card. **The record that it was
    answered, and nothing about what they said.**"""

    __tablename__ = "sportsmanship_card"

    game_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    rater_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    #: When the card was closed. There is no ``updated_at`` and no ``state``: a
    #: card is answered or it does not exist.
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SportsmanshipRatingORM(Base):
    """What one player currently thinks of another. **One row per pair, ever.**"""

    __tablename__ = "sportsmanship_rating"
    __table_args__ = (
        ForeignKeyConstraint(
            ["game_id", "rater_id"],
            ["sportsmanship_card.game_id", "sportsmanship_card.rater_id"],
            name="fk_sportsmanship_rating_card",
            ondelete="RESTRICT",
        ),
        # The published fold's only read: *who has an opinion about this person,
        # most recent first*. The date is in the index because the window is
        # always applied — it is fifty raters, and taking the fifty most recent
        # of them is an ordering before it is a limit.
        Index(
            "ix_sportsmanship_rating_about",
            "subject_id",
            "rated_at",
        ),
        # **A check constraint, not a convention.** You rate everybody else on
        # the court, and the write path cannot produce a self-rating — the rater
        # is not among the others a court offers — so this refuses one that
        # arrived any other way.
        CheckConstraint(
            "rater_id <> subject_id",
            name="ck_sportsmanship_rating_not_about_yourself",
        ),
        # One to five whole stars. The rule's home is the domain; this is the
        # database refusing to hold a value that rule would not have produced.
        CheckConstraint(
            "stars BETWEEN 1 AND 5",
            name="ck_sportsmanship_rating_is_one_to_five_stars",
        ),
    )

    rater_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    subject_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    #: Which card this standing answer came from. A column and not a key: the
    #: answer belongs to the pair, and the game says which evening produced the
    #: one that stands.
    game_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    stars: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
