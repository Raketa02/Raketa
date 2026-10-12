/**
 * **Who's here, at a booked game's court** — what the attendance block offers a reader and says
 * about each player ([#658](https://github.com/Raketa02/Raketa/issues/658); ADR-0195 §3; the
 * backend's #657).
 *
 * Only a real absence starts anything. In the **first half hour** a player at the club taps *Oscar
 * isn't here yet* about anybody else on the court, partner included; Oscar's **arrival** is the first
 * *I'm here* or *they're here*. Afterwards a player who Didn't come has one way back — *I was there*
 * within a day, which somebody else on the court confirms with *Yes, they were here*. Everybody who
 * arrives on time does nothing at all.
 *
 * **Nothing here folds an outcome.** On time, Came late and Didn't come are the backend's, folded
 * against the list's `readAt` and carried on each row; what is decided here is only which controls
 * to draw and what to say beside whom.
 *
 * ## The first half hour is the one window this side measures
 *
 * Before anybody is tapped the wire carries no window: `GameSchema` has no hour, and `arrive_by`
 * arrives on a row. So the composer of a booked game's screen hands its booking's hour in
 * ({@link BookedHour}), and the window is read off it against `readAt` — the backend's
 * `TAP_WINDOW`, a number promised to players (ADR-0195 §3). A list read before the window and still
 * on screen after it offers a tap the backend refuses with `the_tap_window_has_closed`, which the
 * block says in a sentence.
 *
 * ## The reader's own act is not a row
 *
 * *I'm here* and *I was there* are what the screen is for while they are offered, so they are
 * {@link AttendanceBlock.own} and pinned, as the score's send is. The rows are about everybody else
 * — and the reader's own *Came late*, which nothing else on the screen says.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';

import type { Attendance, Game } from './game';
import { NOT_HERE, whoIs } from './resultArgument';
import type { GameStanding } from './vocabulary';

/**
 * **Where the phone was at the moment of a tap** — one precise fix, read then and sent with the tap
 * (ADR-0195 §3). The backend measures it against the club's map point and keeps only *at the club*;
 * nothing on this side keeps it either — it goes out of scope with the request it rode on.
 * `accuracyMetres` is the fix's own stated accuracy, `null` where the platform states none.
 */
export interface TapPosition {
  readonly latitude: number;
  readonly longitude: number;
  readonly accuracyMetres: number | null;
}

/**
 * **Why the phone could not say where it was at a tap** — the permission refused (and the OS will
 * ask again), refused for good (only Settings changes it), or no fix produced, and nothing was
 * sent; or **a fix too rough for the check** ({@link isRoughFix}), which the backend found not at
 * the club.
 */
export type LocationRefusal = 'refused' | 'blocked' | 'no-fix' | 'rough';

/**
 * How much of a fix's own stated accuracy the club's check allows for — the backend's
 * `ACCURACY_ALLOWED_UP_TO_M` (ADR-0195 §3). Read here for one sentence and never for a verdict: a
 * fix wider than this is still sent, and the backend still decides.
 */
const ALLOWED_FOR_UP_TO_M = 200;

/**
 * **A fix wider than the check allows for** — the likeliest reason a player standing at the club is
 * told they are not: a phone sharing only an approximate position (iOS with Precise Location off,
 * Android's approximate location), or a first fix indoors. A fix that states no accuracy is not
 * known to be rough.
 */
export function isRoughFix(at: TapPosition): boolean {
  return at.accuracyMetres !== null && at.accuracyMetres > ALLOWED_FOR_UP_TO_M;
}

/** **The booked hour, as its booking knows it** — handed in by whoever composes the screen. */
export interface BookedHour {
  readonly startsAt: string;
}

/** How long after the start *isn't here yet* and an arrival are taken: the first half of the hour. */
export const TAP_WINDOW_MS = 30 * 60 * 1000;

/**
 * **Whether the first half hour is running at `at`** — from the start, until half an hour after it
 * and never at that moment: an arrival at exactly 17:30 is refused, as the backend's window is
 * half-open. An hour this build cannot read is never open.
 */
export function tapsAreOpen(startsAt: string, at: string | number): boolean {
  const start = Date.parse(startsAt);
  const now = typeof at === 'number' ? at : Date.parse(at);
  if (Number.isNaN(start) || Number.isNaN(now)) return false;
  return now >= start && now < start + TAP_WINDOW_MS;
}

/** A tap about somebody else, made at the club — or the confirmation of their late claim. */
export type AttendanceTap =
  /** *Oscar isn't here yet* — nobody has said so of them, and the half hour runs. */
  | 'not-here-yet'
  /** *Oscar is here* — they are awaited, and walked in. */
  | 'here'
  /** *Yes, Oscar was here* — they said *I was there*, and their day runs. */
  | 'was-here';

/** What the block says beside somebody. */
export type AttendanceSaid =
  /** Awaited, and this reader may not say they arrived — they are awaited themselves. */
  | 'not-here-yet'
  /** Arrived ten to thirty minutes after the start, or *I was there* confirmed. */
  | 'came-late'
  /** Said *I was there*, and nobody has confirmed it yet. */
  | 'says-they-were-there';

/** **One player on the block** — what is said of them, the tap about them, or both. */
export interface AttendanceRow {
  readonly playerId: string;
  /** *You* on the reader's own row, the whole name, or `?` where `users` lost them. */
  readonly who: NamedPlayer;
  readonly said?: AttendanceSaid;
  readonly tap?: AttendanceTap;
}

/** The reader's own act, pinned while it is offered. */
export type OwnAttendanceAct = 'im-here' | 'i-was-there';

export interface AttendanceBlock {
  /** **In the first half hour, or after it** — the block's heading is keyed on it. */
  readonly phase: 'at-the-court' | 'afterwards';
  /** In the court's order. Nobody is on it with nothing said and nothing to press. */
  readonly rows: readonly AttendanceRow[];
  readonly own?: OwnAttendanceAct;
}

/**
 * **The standings a tap at the court is taken on** — nobody has said it happened, a score waits for
 * its answer (a waiting score stops no tap, or the absent side could post one from home and never be
 * caught), or somebody is already awaited. A settled result refuses one, and so does a game that was
 * called off or started short.
 */
const TAKES_A_TAP: ReadonlySet<GameStanding> = new Set<GameStanding>([
  'AWAITING_ENTRY',
  'AWAITING_ANSWER',
  'NOT_HERE_YET',
]);

/** **The block, for this reader** — `hour` is the booking's, absent on a game nobody booked. */
export function attendanceBlock(
  game: Game,
  reader: string,
  hour: BookedHour | undefined,
): AttendanceBlock {
  const rowOf = (playerId: string): Attendance | undefined =>
    game.attendance.find((one) => one.playerId === playerId);
  const yours = rowOf(reader)?.state;
  const readerIsHere = yours === undefined || !NOT_HERE.has(yours);

  const atTheCourt = hour !== undefined && tapsAreOpen(hour.startsAt, game.readAt);
  const mayTap =
    atTheCourt && readerIsHere && game.standing !== undefined && TAKES_A_TAP.has(game.standing);
  const readAt = Date.parse(game.readAt);
  const dayRuns = (row: Attendance) => readAt < Date.parse(row.claimBy);

  const rows = game.seats.flatMap((seat): AttendanceRow[] => {
    if (seat.playerId === undefined) return [];
    const playerId = seat.playerId;
    const who = whoIs(game, reader, playerId);
    const row = rowOf(playerId);
    const drawn = (said?: AttendanceSaid, tap?: AttendanceTap): AttendanceRow[] =>
      said === undefined && tap === undefined
        ? []
        : [
            {
              playerId,
              who,
              ...(said === undefined ? {} : { said }),
              ...(tap === undefined ? {} : { tap }),
            },
          ];

    if (playerId === reader) {
      // The reader's own wait and their Didn't come are the screen's heading and its pinned act.
      return row?.state === 'CAME_LATE' || row?.state === 'CONFIRMED' ? drawn('came-late') : [];
    }
    if (row === undefined) return drawn(undefined, mayTap ? 'not-here-yet' : undefined);

    switch (row.state) {
      case 'WAITING':
        return mayTap ? drawn(undefined, 'here') : drawn('not-here-yet');
      case 'CAME_LATE':
      case 'CONFIRMED':
        return drawn('came-late');
      case 'CLAIMED':
        return drawn('says-they-were-there', readerIsHere && dayRuns(row) ? 'was-here' : undefined);
      // On time vanishes; a Didn't come is the standing line's; a code this build cannot read says
      // nothing rather than something wrong.
      case 'ON_TIME':
      case 'DIDNT_COME':
      case undefined:
        return [];
    }
  });

  const own = ownAct(rowOf(reader), readAt);
  return {
    phase: atTheCourt ? 'at-the-court' : 'afterwards',
    rows,
    ...(own === undefined ? {} : { own }),
  };
}

/**
 * *I'm here* while the reader is awaited, and *I was there* while they Didn't come and their day to
 * say so runs — never once they have said it, when it waits on somebody else.
 */
function ownAct(row: Attendance | undefined, readAt: number): OwnAttendanceAct | undefined {
  if (row?.state === 'WAITING') return 'im-here';
  if (row?.state === 'DIDNT_COME' && readAt < Date.parse(row.claimBy)) return 'i-was-there';
  return undefined;
}
