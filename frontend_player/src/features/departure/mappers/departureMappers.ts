/**
 * The wire's departure screen, mapped into this feature's vocabulary.
 *
 * One of the two layers allowed to read generated types, and the layer that turns
 * a **code into a sentence** — an outcome label, a standing, and the match's own
 * situation, which is resolved through **Now's** table rather than a second one.
 * That import is the point: the wire embeds the match's spine and situation half
 * *verbatim*, so the screen she arrives on cannot describe the match differently
 * from the card she tapped, and a table of thirty-six sentences copied here would
 * be the two disagreeing in whichever one shipped last.
 *
 * **Nothing is computed.** No total, no count, no comparison against the clock, no
 * inference from an absent field. The one derivation the phone is allowed is
 * subtracting a moment from the current time, and this feature reaches Now's
 * `countdown` for it rather than holding a second one.
 *
 * **A widened wire union fails here first.** `Cover` and `Currency` are assigned
 * into the narrower types this app owns, exactly as Now's mapper does, so a third
 * cover or a second currency is a `pnpm typecheck` failure in a diff where
 * somebody has to decide what it looks like.
 */

import type { components } from '@/generated/schema';
import type { Cover, Place } from '@/features/now/types';
import { situationCopy, toNowUpdate } from '@/features/now/types';
import type { Currency, Money } from '@/shared/lib/formatting';
import { formatMoney } from '@/shared/lib/formatting';

import type {
  Departure,
  DepartureAnswer,
  OutcomeRow,
  Quote,
  SeatCounts,
} from '../domain/Departure';

import { outcomeCopy, standingCopy } from './outcomes';

type DepartureScreenResponse = components['schemas']['DepartureScreenResponse'];
type DepartureWriteResponse = components['schemas']['DepartureWriteResponse'];
type OutcomeRowResponse = components['schemas']['OutcomeRowResponse'];
type PlaceResponse = components['schemas']['PlaceResponse'];
type MoneyResponse = components['schemas']['MoneyResponse'];
type SeatCountsResponse = components['schemas']['SeatCountsResponse'];

export function toDeparture(wire: DepartureScreenResponse): Departure {
  const price = toMoney(wire.price);
  const where = toPlace(wire.where);

  return {
    matchId: wire.match_id,
    where,
    price,
    situation: wire.situation.situation,
    // Now's own table, given the spine's two printable facts — the same context a
    // card is resolved with, so the sentence on this screen is the sentence on the
    // card. A situation this build cannot name loses the line and nothing else.
    status: situationCopy(wire.situation.situation, {
      facts: wire.situation.facts,
      clubName: where.clubName,
      price: formatMoney(price),
    }),
    mayDepart: wire.may_depart,
    quote: toQuote(wire.quote),
    outcomes: wire.outcomes.map(toOutcomeRow),
    counts: toSeatCounts(wire.counts),
    commitmentDeadline: wire.commitment_deadline ?? undefined,
  };
}

/**
 * A write's answer: the screen, what the tap did, and Now's update.
 *
 * `applied` is `undefined` **exactly** when nothing was applied, which is the only
 * thing its absence can mean. It is what stops *was I refused* being a rule on the
 * phone: deriving it from `mayDepart` still being true would be one, and
 * `ADR-0053` leaves the phone none.
 */
export function toDepartureAnswer(wire: DepartureWriteResponse): DepartureAnswer {
  return {
    screen: toDeparture(wire.screen),
    applied: wire.applied == null ? undefined : toQuote(wire.applied),
    update: toNowUpdate(wire.update),
  };
}

/**
 * The label, and what it means — kept together so the write cannot send words.
 *
 * `outcome` rides back on the `POST` unread and unmodified: it is what she was
 * shown as the basis for deciding, and the server refuses if the live outcome has
 * become strictly worse than it.
 */
function toQuote(outcome: string): Quote {
  return { outcome, copy: outcomeCopy(outcome) };
}

function toOutcomeRow(wire: OutcomeRowResponse): OutcomeRow {
  return {
    outcome: wire.outcome,
    name: outcomeCopy(wire.outcome)?.name,
    standing: standingCopy(wire.standing),
    // Carried across as it arrived. The server sends it on exactly one standing,
    // and this does not check that: a phone that policed the pairing would be
    // holding a rule about the server's own composition.
    opensAt: wire.opens_at ?? undefined,
  };
}

/**
 * Three numbers, and `turned_up` is not one of them.
 *
 * It is present once a match has been **played**, and a match that has been played
 * cannot be left — so mapping it here would be a field kept warm for a screen that
 * cannot render it.
 */
function toSeatCounts(wire: SeatCountsResponse): SeatCounts {
  return { seats: wire.seats, paid: wire.paid, held: wire.held };
}

function toPlace(wire: PlaceResponse): Place {
  const cover: Cover = wire.cover;

  return {
    clubId: wire.club_id,
    clubName: wire.club_name,
    zone: wire.zone,
    cover,
    distanceKm: wire.distance_km ?? undefined,
  };
}

function toMoney(wire: MoneyResponse): Money {
  const currency: Currency = wire.currency;
  return { amount: wire.amount, currency };
}
