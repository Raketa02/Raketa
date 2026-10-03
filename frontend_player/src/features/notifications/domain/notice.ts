/**
 * **A notice — one thing a player was told** (#559; the screens A9; the mechanics §17.2): its words
 * as the push said them, when it was given, and **where a tap opens it**.
 *
 * The words are the backend's (`application/words.py`), drawn at push time and again at every read:
 * the phone's system draws a push before the app runs, so the sentence cannot be the app's. What
 * the app decides is where a tap goes, and how *when* is said.
 */

import type { GameKind } from '@/features/proposals/types';
import { daysBetween, platformClock, platformDay, weekdayOf } from '@/shared/date/platformZone';
import type { Sport } from '@/shared/vocabulary/sport';
import type { Weekday } from '@/shared/vocabulary/week';

import type { NoticeKind, Opens } from './vocabulary';

/**
 * Where a tap goes. A booked game is read by its booking, whose id is the game's own (#541); a game
 * still filling and a card on a deck are both in the group the pool is filed under, in a sport and a
 * kind — the deck is the read for exactly those, and a game's details draw the card that read dealt.
 */
export type NoticeTarget =
  | { readonly opens: 'booking'; readonly bookingId: string }
  | { readonly opens: 'rescue'; readonly groupId: string; readonly bookingId: string }
  | {
      readonly opens: 'game' | 'deck';
      readonly groupId: string;
      readonly proposalId: string;
      readonly sport: Sport;
      readonly kind: GameKind;
    };

/** What a notice names, whichever way it arrived — the list's row or a push's payload. */
export interface NoticeFacts {
  readonly gameId: string;
  readonly poolId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
}

/**
 * **Where a tap opens** (A9): `BOOKING` the booked game's details, `PROPOSAL` the game's details in
 * its group — one still filling, or one that did not fill — and `DECK` the group's deck in the
 * card's sport and kind, **with the card on top**: *You complete it* and a challenge are a card
 * waiting for the player, and the deck is where it is answered.
 *
 * **A Fill in alert is the one notice whose kind decides**: the backend sends it as `BOOKING` — the
 * booked game — to a reader who is **not in it**, so its details are the ones a *Seats to fill* row
 * opens, the open seat seen from outside, in its group (A4.3). The booked game's own details would
 * tell a reader who was never in it that the game is not theirs any more.
 */
export function targetOf(kind: NoticeKind, opens: Opens, facts: NoticeFacts): NoticeTarget {
  if (opens === 'BOOKING' && kind === 'FILL_IN_ALERT') {
    return { opens: 'rescue', groupId: facts.poolId, bookingId: facts.gameId };
  }
  if (opens === 'BOOKING') return { opens: 'booking', bookingId: facts.gameId };
  return {
    opens: opens === 'PROPOSAL' ? 'game' : 'deck',
    groupId: facts.poolId,
    proposalId: facts.gameId,
    sport: facts.sport,
    kind: facts.kind,
  };
}

export interface Notice {
  readonly id: string;
  readonly kind: NoticeKind;
  readonly title: string;
  readonly body: string;
  /** When it was given — or when the day last bundled another into it, which moves it up. */
  readonly givenAt: string;
  /** Where a tap goes — absent for a game in a sport this build cannot name. */
  readonly target?: NoticeTarget;
}

/**
 * **When a notice was given, as the list says it** — by the platform's calendar, never the hours
 * since: *today* is its clock, *yesterday* is said so, a day within the week its weekday, and
 * anything older its date. `undefined` for a time that is not one, which says nothing rather than a
 * guess.
 */
export type GivenWhen =
  | { readonly day: 'today' | 'yesterday'; readonly clock: string }
  | { readonly day: 'weekday'; readonly weekday: Weekday; readonly clock: string }
  | { readonly day: 'date'; readonly date: string; readonly clock: string };

/** A week back, a weekday still names one day; past it, a date does. */
const A_WEEK = 7;

export function givenWhen(givenAt: string, now: string): GivenWhen | undefined {
  const given = platformDay(givenAt);
  const today = platformDay(now);
  const clock = platformClock(givenAt);
  if (given === undefined || today === undefined || clock === undefined) return undefined;

  const ago = daysBetween(given, today);
  if (ago === undefined) return undefined;
  if (ago <= 0) return { day: 'today', clock };
  if (ago === 1) return { day: 'yesterday', clock };
  const weekday = weekdayOf(given);
  if (ago < A_WEEK && weekday !== undefined) return { day: 'weekday', weekday, clock };
  return { day: 'date', date: given, clock };
}
