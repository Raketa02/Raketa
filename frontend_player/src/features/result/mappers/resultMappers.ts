/**
 * The wire's result screen, mapped into this feature's vocabulary.
 *
 * One of the two layers allowed to read generated types, and the layer that turns
 * a **code into a sentence** — here that is the match's own situation, resolved
 * through **Now's** table rather than a second one. That import is the point: the
 * wire embeds the match's spine and situation half *verbatim*, so the screen she
 * arrives on cannot describe the match differently from the card she tapped, and a
 * table of thirty-six sentences copied here would be the two disagreeing in
 * whichever one shipped last.
 *
 * **Nothing is computed.** No total, no count, no comparison against the clock, no
 * inference from an absent field, and — most of all — **no winner**. Who won is not
 * a fact the phone was sent, and working it out from the sets would be the level
 * movement `ADR-0049` refuses arriving through a mapper.
 *
 * **A widened wire union fails here first.** `Cover` and `Currency` are assigned
 * into the narrower types this app owns, exactly as Now's mapper does, so a third
 * cover or a second currency is a `pnpm typecheck` failure in a diff where somebody
 * has to decide what it looks like.
 */

import type { components } from '@/generated/schema';
import type { Cover, Place, ScoreLine } from '@/features/now/types';
import { situationCopy, toNowUpdate } from '@/features/now/types';
import type { Currency, Money } from '@/shared/lib/formatting';
import { formatMoney } from '@/shared/lib/formatting';

import type { Result, ResultAnswer, ResultBlock, SeatCounts } from '../domain/Result';

import { endingCopy } from './endings';

type ResultScreenResponse = components['schemas']['ResultScreenResponse'];
type ResultWriteResponse = components['schemas']['ResultWriteResponse'];
type ResultBlockResponse = components['schemas']['ResultBlockResponse'];
type ScoreLineResponse = components['schemas']['ScoreLineResponse'];
type SeatCountsResponse = components['schemas']['SeatCountsResponse'];
type PlaceResponse = components['schemas']['PlaceResponse'];
type MoneyResponse = components['schemas']['MoneyResponse'];

export function toResult(wire: ResultScreenResponse): Result {
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
    // How it ended, on the two situations that end it. Resolved from the same name
    // the line above was, so the ending and the sentence cannot disagree.
    ending: endingCopy(wire.situation.situation),
    result: toResultBlock(wire.result),
    counts: toSeatCounts(wire.counts),
    mayEnter: wire.may_enter,
    mayAccept: wire.may_accept,
    mayCounter: wire.may_counter,
    settlementDeadline: wire.settlement_deadline ?? undefined,
    acceptanceGrace: wire.acceptance_grace ?? undefined,
  };
}

/** A write's answer: the screen it produced, and Now's update. */
export function toResultAnswer(wire: ResultWriteResponse): ResultAnswer {
  return { screen: toResult(wire.screen), update: toNowUpdate(wire.update) };
}

/**
 * The four facts, carried across.
 *
 * `score` and `proposedBy` are absent **together** — the wire sends one exactly
 * when it sends the other — and neither is inferred from the other here: reading
 * `proposed_by` off *whether there is a score* would be the phone re-deriving a
 * pairing the server already states, and it would be silently wrong the day the
 * server sent a score with no proposer.
 */
function toResultBlock(wire: ResultBlockResponse): ResultBlock {
  return {
    agreed: wire.agreed,
    proposals: wire.proposals,
    score: wire.score == null ? undefined : toScoreLine(wire.score),
    proposedBy: wire.proposed_by ?? undefined,
  };
}

/**
 * The score, sides and sets in the order they arrived.
 *
 * The viewer's side is already first — the server put it there — and this feature
 * neither flips it nor checks that it was flipped. Two answers to *whose 6 was
 * that* is the failure naming the sides exists to prevent.
 */
function toScoreLine(wire: ScoreLineResponse): ScoreLine {
  return {
    sides: wire.sides.map((side) => ({ players: side.players })),
    sets: wire.sets.map((set) => ({ first: set.first, second: set.second })),
  };
}

/**
 * Four numbers, and `turnedUp` is one of them here.
 *
 * The departure screen drops it, because a match that has been played cannot be
 * left; this screen is about a match that **has** been played, so it is the one
 * surface where *three of four turned up* is a fact the player is owed — and it is
 * sent rather than derived for the reason the contract states, that *one less than
 * the seats* stops being minus one the moment a doubles match loses two people.
 */
function toSeatCounts(wire: SeatCountsResponse): SeatCounts {
  return {
    seats: wire.seats,
    paid: wire.paid,
    held: wire.held,
    turnedUp: wire.turned_up ?? undefined,
  };
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
