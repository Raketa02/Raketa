from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.events import (
    EventDispatcher,
    EventCatalog,
)
from app.application.events.deliver_event_batch import EventBatch
from app.core.config import Settings, get_settings
from app.infrastructure.clock import SystemClock
from app.infrastructure.events.event_delivery_worker import (
    EventWorker,
)
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.infrastructure.events.sqlalchemy_domain_event_store import (
    SqlAlchemyEventStore,
)
from app.infrastructure.events.sqlalchemy_event_delivery_queue import (
    SqlAlchemyOutboxRepository,
)
from app.infrastructure.events.transactional_publisher import (
    EventPublisher,
)
from app.kernel import Clock
from app.modules.conversations.domain.live import NudgePublisher
from app.modules.administrators.application.event_subscriptions import (
    register_administrator_events,
    subscribe_administrator_handlers,
)
from app.modules.auth.application.event_subscriptions import (
    register_auth_events,
    subscribe_auth_handlers,
)
from app.modules.bookings.application.event_subscriptions import (
    register_booking_events,
    subscribe_booking_handlers,
)
from app.modules.blocks.application.event_subscriptions import (
    register_block_events,
    subscribe_block_handlers,
)
from app.modules.clubs.application.event_subscriptions import (
    register_club_events,
    subscribe_club_handlers,
)
from app.modules.groups.application.event_subscriptions import (
    register_group_events,
    subscribe_group_handlers,
)
from app.modules.conversations.application.event_subscriptions import (
    register_conversation_events,
    subscribe_conversation_handlers,
    subscribe_the_room_teller,
)
from app.modules.games.application.event_subscriptions import (
    register_game_events,
    subscribe_game_handlers,
)
from app.modules.payments.application.event_subscriptions import (
    register_payment_events,
    subscribe_payment_handlers,
    subscribe_the_method_releaser,
    subscribe_the_club_payout_sender,
    subscribe_the_seat_charge_settler,
)
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.notifications.application.event_subscriptions import (
    register_notification_events,
    subscribe_notification_handlers,
    subscribe_the_pusher,
    subscribe_the_teller,
)
from app.modules.notifications.domain.ports import PushNotifications
from app.modules.proposals.application.propose_games import DueForProposing
from app.modules.proposals.application.event_subscriptions import (
    register_proposal_events,
    subscribe_proposal_handlers,
    subscribe_the_blocker,
    subscribe_the_pool_leaver,
    subscribe_the_proposer_on_changes,
    subscribe_the_week_resumer,
)
from app.modules.player_profile.application.event_subscriptions import (
    register_player_profile_events,
    subscribe_player_profile_handlers,
)
from app.modules.rating.application.event_subscriptions import (
    register_rating_events,
    subscribe_rating_handlers,
)
from app.modules.users.application.event_subscriptions import (
    register_user_events,
    subscribe_user_handlers,
)


@dataclass(frozen=True)
class EventRuntime:
    codec: JsonEventCodec
    dispatcher: EventDispatcher
    #: The durable-name register the codec was built over.
    #:
    #: Carried beside the codec rather than left inside it so a reader can walk
    #: every registered event class — ``test_every_event_has_a_subscriber`` asks
    #: it which classes exist and the dispatcher who hears each. The candidate
    #: index that first needed the mapping went with the ranking (#580).
    catalog: EventCatalog

    def create_publisher_for(self, *, session: AsyncSession) -> EventPublisher:
        return EventPublisher(
            outbox=SqlAlchemyOutboxRepository(session), codec=self.codec
        )

    def create_domain_event_store_for(
        self, *, session: AsyncSession
    ) -> SqlAlchemyEventStore:
        return SqlAlchemyEventStore(session, self.codec)

    def create_event_batch_for(
        self,
        *,
        session: AsyncSession,
        clock: Clock,
        batch_size: int,
        nudges: NudgePublisher,
        payments: PaymentProvider,
        push: PushNotifications,
        proposer_due: DueForProposing | None = None,
    ) -> EventBatch:
        """One batch of the outbox, over this session.

        **``nudges`` is required and reaches exactly one subscriber**, which is
        the room teller. It is threaded through this generic loop rather than
        resolved from the process because *is this delivery live* is a fact about
        the run and not about the machinery: an API process has phones attached
        to it, a seed run and a command-line drain do not, and a default here
        would make the quiet answer the one nobody chose. That it is a
        conversation's port in a shared loop is a coupling this class already
        carries — ``_dispatcher_over`` below exists for the same subscriber.

        **``payments`` is required on the same argument**, and reaches the one
        subscriber that releases a replaced or removed card at the provider: the
        API's delivery holds the provider its requests hold, a seed run's holds
        the fake it saved its cards through, and a default here would be a
        release sent somewhere nobody chose.

        **``push`` is required on the same argument** (#549): a notice given is
        pushed to its player's phones by the pusher this run holds — the API's
        Expo, a seed run's recording service, whose players have no phones —
        and a default here would be phones pushed, or not, by nobody's choice.

        **``proposer_due`` is the one that may be absent**: it is where this
        process's proposer is told what changed (#540), and a seed run or a
        command-line drain has no proposer listening. Absent is a real answer —
        the proposer's sweep sees every change anyway — so it defaults to it.
        """

        # See ``_dispatcher_over`` for why the composition root is reached at
        # call time here: ``composition`` imports this module, so the arrow
        # already runs the other way.
        from app.bootstrap.composition import build_unit_of_work

        return EventBatch(
            outbox=SqlAlchemyOutboxRepository(session),
            codec=self.codec,
            dispatcher=self._dispatcher_over(
                session,
                clock=clock,
                nudges=nudges,
                payments=payments,
                push=push,
                proposer_due=proposer_due,
            ),
            uow=build_unit_of_work(session),
            clock=clock,
            batch_size=batch_size,
        )

    def _dispatcher_over(
        self,
        session: AsyncSession,
        *,
        clock: Clock,
        nudges: NudgePublisher,
        payments: PaymentProvider,
        push: PushNotifications,
        proposer_due: DueForProposing | None = None,
    ) -> EventDispatcher:
        """The process's subscriptions, plus the ones that need this batch's session.

        **Every subscriber was a logger until the Conversation context arrived**
        (``docs/adr/0146`` §5), and a logger needs nothing per delivery. A
        subscriber that *writes* needs the session ``EventBatch`` will mark the
        outbox row published in, so that a system line and the delivery that
        caused it commit together — which is a per-tick fact and cannot be
        registered on a dispatcher built once for the process.

        The copy is what stops one tick's handlers accumulating on the next.

        **The composition root is imported here rather than at the top**, and it
        is the one local import in this file: ``composition`` imports this module
        for ``EventRuntime``, so the arrow already runs the other way. Reaching
        for the two builders at call time keeps *what is built* in the one place
        that decides it, without inverting a dependency the rest of the file
        depends on.
        """

        from app.bootstrap.composition import (
            build_push_the_notice,
            build_resume_paused_yeses,
            build_send_club_payout,
            build_settle_seat_charges,
            build_tell_the_players,
            build_tell_the_room,
            build_withdraw_a_blockers_yeses,
            build_withdraw_a_leavers_yeses,
        )

        dispatcher = self.dispatcher.copy()
        subscribe_the_room_teller(
            dispatcher, build_tell_the_room(session, nudges=nudges)
        )
        subscribe_the_method_releaser(dispatcher, payments)
        # A fill's verdict, captured or cancelled at the provider — written onto
        # the charge in the delivery's own transaction (#541).
        subscribe_the_seat_charge_settler(
            dispatcher,
            build_settle_seat_charges(
                session, provider=payments, clock=clock, runtime=self
            ),
        )
        # A club's payout, made at the provider and told to its desk in the
        # delivery's own transaction (#548).
        subscribe_the_club_payout_sender(
            dispatcher,
            build_send_club_payout(
                session,
                provider=payments,
                clock=clock,
                settings=get_settings(),
                runtime=self,
            ),
        )
        # A leaver's yeses are withdrawn in the transaction that delivers the
        # leaving, so this one needs the batch's session too — and a request a
        # game of theirs waits on goes with them (#543).
        subscribe_the_pool_leaver(
            dispatcher,
            build_withdraw_a_leavers_yeses(
                session, settings=get_settings(), runtime=self
            ),
        )
        # A blocker's yeses where the blocked player is In are taken back in the
        # transaction that delivers the block — and a request a waiting game of
        # theirs had put to its club goes with them (`docs/adr/0193` §4).
        subscribe_the_blocker(
            dispatcher,
            build_withdraw_a_blockers_yeses(
                session, settings=get_settings(), runtime=self
            ),
        )
        # A paused week comes back when a booked game stops being a player's —
        # and a yes that comes back as a game's last seat fills it, over this
        # run's provider (#544).
        subscribe_the_week_resumer(
            dispatcher,
            build_resume_paused_yeses(
                session, provider=payments, settings=get_settings(), runtime=self
            ),
        )
        # What players are told about a game and its money, given in the
        # delivery's own transaction — and a notice given, pushed to their
        # phones over this run's push service (#549).
        subscribe_the_teller(
            dispatcher,
            build_tell_the_players(session, settings=get_settings(), runtime=self),
        )
        subscribe_the_pusher(
            dispatcher,
            build_push_the_notice(session, push=push, clock=clock, runtime=self),
        )
        # And what changed, for this process's proposer, when one is listening.
        if proposer_due is not None:
            subscribe_the_proposer_on_changes(dispatcher, proposer_due)
        return dispatcher


def build_event_runtime() -> EventRuntime:
    catalog = EventCatalog()
    register_user_events(catalog)
    register_auth_events(catalog)
    register_rating_events(catalog)
    register_player_profile_events(catalog)
    register_block_events(catalog)
    register_game_events(catalog)
    register_conversation_events(catalog)
    register_club_events(catalog)
    register_group_events(catalog)
    register_administrator_events(catalog)
    register_payment_events(catalog)
    register_proposal_events(catalog)
    register_booking_events(catalog)
    register_notification_events(catalog)

    dispatcher = EventDispatcher()
    subscribe_user_handlers(dispatcher)
    subscribe_auth_handlers(dispatcher)
    subscribe_rating_handlers(dispatcher)
    subscribe_player_profile_handlers(dispatcher)
    subscribe_block_handlers(dispatcher)
    subscribe_game_handlers(dispatcher)
    subscribe_conversation_handlers(dispatcher)
    subscribe_club_handlers(dispatcher)
    subscribe_group_handlers(dispatcher)
    subscribe_administrator_handlers(dispatcher)
    subscribe_payment_handlers(dispatcher)
    subscribe_proposal_handlers(dispatcher)
    subscribe_booking_handlers(dispatcher)
    subscribe_notification_handlers(dispatcher)

    return EventRuntime(
        codec=JsonEventCodec(catalog),
        dispatcher=dispatcher,
        catalog=catalog,
    )


@lru_cache(maxsize=1)
def get_event_runtime() -> EventRuntime:
    """The process's event runtime, built once and reachable from anywhere.

    It used to be reachable only as `request.app.state.event_runtime`, which
    made the domain-event machinery a property of a *served HTTP request* rather
    than of the process — so a seed run or a management command could only get
    one by booting the API or by building a second, parallel runtime.

    Cached, and safe to cache, because `EventRuntime` is frozen and what it
    holds is declarative: a catalog of event names and a table of handler
    subscriptions, both registered from static code. Nothing about it varies per
    request, and nothing mutates it after `build_event_runtime` returns.
    `build_event_runtime` stays public and uncached for the callers that
    genuinely want a fresh one — a test asserting on a codec in isolation.

    Cached the same way `get_settings` is, and with the same escape hatch:
    `get_event_runtime.cache_clear()`.
    """
    return build_event_runtime()


def build_event_delivery_worker(
    *,
    event_runtime: EventRuntime,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    nudges: NudgePublisher,
    payments: PaymentProvider,
    push: PushNotifications,
    clock: Clock | None = None,
    proposer_due: DueForProposing | None = None,
) -> EventWorker:
    """The embedded outbox drain. **This is the delivery that is live.**

    It runs inside the API process, beside the streams, so the system lines it
    writes reach open conversations without anybody refreshing — which is what
    ``nudges`` is, and why it has no default here either. ``push`` is the push
    service a notice reaches a phone through. ``proposer_due`` is this
    process's proposer, told what the delivery changed.
    """

    processing_clock = clock or SystemClock()
    return EventWorker(
        session_factory=session_factory,
        batch_factory=lambda session: event_runtime.create_event_batch_for(
            session=session,
            clock=processing_clock,
            batch_size=settings.EVENT_DELIVERY_BATCH_SIZE,
            nudges=nudges,
            payments=payments,
            push=push,
            proposer_due=proposer_due,
        ),
        poll_interval_seconds=settings.EVENT_DELIVERY_POLL_INTERVAL_SECONDS,
    )
