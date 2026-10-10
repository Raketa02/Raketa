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
 * card's sport and kind, **with the card on top**: *You complete it*, a challenge and *Your new
 * game* (Q107) are a card waiting for the player, and the deck is where it is answered. *It's a
 * game! · Kazimierz Padel answers by 21:15* (Q103) opens a game still the proposal's — nobody has
 * paid and there is no Game until its club says yes — so its details in the group.
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
  /**
   * It reached the list since the player last opened it, and the bell counts it — the server's
   * answer, the same on every phone (Q101).
   */
  readonly isNew: boolean;
  /**
   * About the player's own act — *It's a game!* for the yes that filled the game, or the seat they
   * took. Born seen: listed, never counted, never the banner (Q102).
   */
  readonly yourOwn: boolean;
  /** Where a tap goes — absent for a game in a sport this build cannot name. */
  readonly target?: NoticeTarget;
}

/** **The list behind the bell, and the bell's number** — one read, so the two always agree. */
export interface RecentNotices {
  /** The newest first. */
  readonly notices: readonly Notice[];
  /** The notices since the player last opened the list, never their own — exact, uncapped. */
  readonly newCount: number;
}

/** What one read of the list brings a session that has read it before. */
export interface Arrivals {
  /** A notice the session had not seen reached the list — Home is read again (Q103). */
  readonly arrived: boolean;
  /** The one drawn as the banner: the newest of them that is not the player's own. */
  readonly banner?: Notice;
}

/**
 * **What a read brings**, against every id the session has seen. A notice the day bundled another
 * into keeps its id and moves up: it is not an arrival, and the backend pushes nothing for it either.
 * **The player's own act is never announced back** (Q102) — it arrives, so Home is read again, and
 * the banner is the newest notice that is somebody else's.
 */
export function arrivalsOf(seen: ReadonlySet<string>, notices: readonly Notice[]): Arrivals {
  const arrivals = notices.filter((notice) => !seen.has(notice.id));
  const banner = arrivals.find((notice) => !notice.yourOwn);
  return { arrived: arrivals.length > 0, ...(banner === undefined ? {} : { banner }) };
}

/**
 * **The rows that stand out on this visit** (Q101): every row a read while the list is open says is
 * new. Held, rather than read off the latest answer: once the visit is recorded the server says
 * none is new, and they stand out for as long as the list is open all the same. The same set back
 * when a read adds nothing.
 */
export function standingOut(
  held: ReadonlySet<string>,
  notices: readonly Notice[],
): ReadonlySet<string> {
  const added = notices.filter((notice) => notice.isNew && !held.has(notice.id));
  if (added.length === 0) return held;
  return new Set([...held, ...added.map((notice) => notice.id)]);
}

/**
 * **A notice as it reached the list** — its id, and when: a notice the day bundled another into keeps
 * its id and reaches the list again, so the bell counts it again.
 */
function reachedAs(notice: Notice): string {
  return `${notice.id}@${notice.givenAt}`;
}

/** **The list behind the bell, while it is open** — what stands out, and what a visit covered. */
export interface OpenList {
  /** The rows standing out — every row a read while it is open has called new. */
  readonly standOut: ReadonlySet<string>;
  /** Each new row, as it reached the list, that a visit sent has covered — none before the first. */
  readonly covered: ReadonlySet<string> | undefined;
}

export const JUST_OPENED: OpenList = { standOut: new Set(), covered: undefined };

/**
 * **A read on the open list** — what stands out after it, and whether the visit follows it (Q101).
 *
 * The read it opens on is from before it was opened, so its rows stand out and **no visit follows
 * it**: the visit marks seen whatever is listed by the time it arrives, and must follow a read of
 * what the list draws. **The first read since opening always sends it** — opening is the visit — and
 * a later one sends it again **only for a new row no visit has covered**: a notice reaching the open
 * list, or one the day bundled into a row already there. Keyed by rows rather than the number, so a
 * visit the server declines to move, which leaves them new, cannot loop.
 */
export function readOnTheOpenList(
  list: OpenList,
  notices: readonly Notice[],
  { sinceOpening }: { readonly sinceOpening: boolean },
): { readonly list: OpenList; readonly visit: boolean } {
  const standOut = standingOut(list.standOut, notices);
  if (!sinceOpening) return { list: { ...list, standOut }, visit: false };
  const uncovered = notices
    .filter((notice) => notice.isNew)
    .map(reachedAs)
    .filter((reached) => list.covered?.has(reached) !== true);
  const visit = list.covered === undefined || uncovered.length > 0;
  const covered = visit ? new Set([...(list.covered ?? []), ...uncovered]) : list.covered;
  return { list: { standOut, covered }, visit };
}

/**
 * **The list as the visit leaves it**: whatever is listed by the time the visit arrives counts as
 * seen, so nothing on it is new and the bell is nought — what the server will answer next, written
 * before it is read again.
 */
export function afterTheVisit(read: RecentNotices): RecentNotices {
  return {
    notices: read.notices.map((notice) => (notice.isNew ? { ...notice, isNew: false } : notice)),
    newCount: 0,
  };
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
