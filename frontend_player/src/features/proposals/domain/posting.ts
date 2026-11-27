/**
 * **Posting a game** — the grid of when a member could post one, a cell's sheet, and the draft the
 * four controls hold ([#558](https://github.com/Raketa02/Raketa/issues/558); the screens A5; the
 * mechanics §9; the backend's #546).
 *
 * Pure. **Everything a cell says is the server's** (`GET /pools/{id}/posting-grid`): how many of the
 * poster's best fits are free together with them at the best hour of the range that has a court,
 * whether a court is free, whether a full game's worth are, whether the poster's own week covers
 * it, whether it is earlier today, and whether a game is already happening there. What is decided
 * here is only how those values are drawn — the nine looks (`cellFill` and its four flags, and the
 * pick, which is the client's) — what a tap may do, and the draft: the controls' choices, kept
 * while the player stays in the group.
 *
 * **The level range narrows and never widens** (Q78). It starts as the engine's own window for the
 * kind around the poster's Level — `engine_level_range`, rounded inward to the hundredth by the
 * server — and is held here as **the narrowed bounds in whole hundredths**, each absent while it
 * stands at the engine's: a press moves one 0,05, worked in hundredths, so no tap drifts off the
 * hundredth; a bound left at the engine's is sent as nothing, so the server reads its own; and the
 * ask never needs the engine's window — only the steppers do, read off the grid on screen.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckCard, DeckPerson } from './deck';
import type { YesOn } from './fill';
import type { SeatToFill } from './fillIn';
import { WHO_ORDER, type DayRange, type GameKind, type Who } from './vocabulary';

/** A range of Levels, both bounds included. */
export interface LevelRange {
  readonly low: number;
  readonly high: number;
}

/** `1` starts today; `2` is the seven days after (A5.2's *‹ This week ›*). */
export type PostingWeek = 1 | 2;

/** **What the controls ask the grid** — the sport, the kind, who it is for and the narrowed bounds. */
export interface PostingAsk {
  readonly sport: Sport;
  readonly kind: GameKind;
  readonly who: Who;
  /** The narrowed lower bound — absent while it stands at the engine's own. */
  readonly levelLow?: number;
  /** The narrowed upper bound — absent while it stands at the engine's own. */
  readonly levelHigh?: number;
}

/** **One day's range on the grid**, as the read says it. */
export interface PostingCell {
  /** The day on the club's clock. */
  readonly day: string;
  readonly range: DayRange;
  /**
   * How many of the poster's best fits are free together with them at `bestStartsAt` — never
   * people who overlap them at different hours.
   */
  readonly fitsFree: number;
  /** The hour the number is read at; absent with no hour ahead. */
  readonly bestStartsAt?: string;
  /** A court the post could be made at is free in the range. */
  readonly courtFree: boolean;
  /** A full game's worth are free: `fitsFree` reaches the open seats. */
  readonly fullGame: boolean;
  /** The poster's own week covers no hour the number could be read at. */
  readonly outsideYourHours: boolean;
  /** Earlier today. */
  readonly past: boolean;
  /** A rescue the poster is offered, or a post still filling they could join, starts in it. */
  readonly happening: boolean;
}

/** **Where a cell is** — a day on the club's clock and a third of it: what a sheet is read for. */
export type CellAt = Pick<PostingCell, 'day' | 'range'>;

/** One column: a day and its three ranges, morning first. */
export interface PostingDay {
  readonly day: string;
  readonly isToday: boolean;
  readonly cells: readonly PostingCell[];
}

/** **WHEN** — one week of the grid. */
export interface PostingGrid {
  readonly week: PostingWeek;
  /** The instant every cell was read against, on the server's clock. */
  readonly readAt: string;
  /** The range the others' Levels were counted in. */
  readonly levelRange: LevelRange;
  /** The engine's own window for the kind — the steppers' starting bounds. */
  readonly engineLevelRange: LevelRange;
  /** The seats besides the poster: three in doubles, one in singles. */
  readonly openSeats: number;
  /** Seven, the first first. */
  readonly days: readonly PostingDay[];
}

/**
 * One of the poster's best fits free then — *2,75 · 93*, or on a For-fun post *2,75 · 67%*: the
 * second figure is the kind's own number (the deck's `headlineOf`, ADR-0207 §5).
 */
export interface SlotFit {
  readonly playerId: string;
  readonly name?: string;
  readonly photoUrl?: string;
  readonly level?: number;
  /** How even a game of the poster and them is forecast. The server sends none on For fun. */
  readonly forecast?: { readonly pct: number };
  /**
   * **On a For-fun post, the Social vibe of the poster and them** (#834), worked out from the two's
   * tags now; the fits come ranked by it. Absent on a competitive post, and where neither holds a
   * tag.
   */
  readonly vibe?: { readonly pct: number };
  /** The reader's own friend — *friend* under the name (#753; Q68). Present only when they are. */
  readonly friend?: true;
}

/** **One *Free courts* row** — a club and hour the post could be made at. */
export interface FreeCourt {
  readonly club: DeckCard['club'];
  /** The group's home club, listed first. */
  readonly homeClub: boolean;
  /** Absent for a poster with no Location area. */
  readonly distanceKm?: number;
  readonly startsAt: string;
  /** *27 zł if it fills*, each. */
  readonly shareGrosze: number;
  /** The latest the post can fill. */
  readonly bookBy: string;
  /** How many courts of the sport are free then. */
  readonly courts: number;
  /** Its own *n free*: the poster's best fits free at this hour (Q77). */
  readonly fitsFree: number;
}

/** **Somebody else's post still filling** that the poster could join — *I'm in*, free until it fills. */
export interface PostStillFilling {
  readonly proposalId: string;
  readonly kind: GameKind;
  readonly startsAt: string;
  readonly club: DeckCard['club'];
  readonly shareGrosze: number;
  readonly bookBy: string;
  /** Who posted it — absent once they withdrew, or for one who can no longer be named. */
  readonly challenger?: DeckCard['challenger'];
  /** Everybody In, in the order they said yes. */
  readonly peopleIn: readonly DeckPerson[];
  readonly openSeats: number;
}

/** **A cell's sheet** (A5.3). */
export interface PostingSlot {
  /** The kind it was read for — which number its fits are lined with (the deck's `headlineOf`). */
  readonly kind: GameKind;
  readonly day: string;
  readonly range: DayRange;
  readonly readAt: string;
  readonly openSeats: number;
  /** The headline's cell. */
  readonly cell: PostingCell;
  /**
   * The best fits free at the cell's best hour, best fit first — on a For-fun post the highest
   * Social vibe first (#834). Drawn in the order served, never re-sorted.
   */
  readonly fits: readonly SlotFit[];
  /** Home club first, then by hour. */
  readonly freeCourts: readonly FreeCourt[];
  /** **Already happening here**, first: booked games with a seat offered to the poster. */
  readonly rescues: readonly SeatToFill[];
  /** Then: posts still filling the poster could join. */
  readonly posts: readonly PostStillFilling[];
}

/** **The post, In with its poster** — its id is the game's, in *You’re in*. */
export interface Posted {
  readonly proposalId: string;
  /** How many versions it was dealt in, up to three. */
  readonly versions: number;
  /** How many best fits were dealt it. */
  readonly dealtTo: number;
  readonly openSeats: number;
}

// ---------------------------------------------------------------------------
// A cell
// ---------------------------------------------------------------------------

/**
 * **The five fills a cell can be** (A5.2): *dead* — nobody who fits is free; *few* and *enough* —
 * some fit, fewer than the open seats or a full game's worth, and no court; *thin* and *hot* — the
 * same with a court. *Outside your hours*, *past*, *your pick* and *happening here* are drawn over
 * whichever it is — the other four of the nine.
 */
export type CellFill = 'dead' | 'few' | 'enough' | 'thin' | 'hot';

export function cellFill(cell: PostingCell): CellFill {
  if (cell.fitsFree === 0) return 'dead';
  if (!cell.courtFree) return cell.fullGame ? 'enough' : 'few';
  return cell.fullGame ? 'hot' : 'thin';
}

/**
 * **Whether a cell's court may be picked** — a court and somebody who fits, and not earlier today.
 * Outside the poster's own week it still may (A5.2): their week is what they said, not a rule.
 */
export function pickable(cell: PostingCell): boolean {
  return !cell.past && cell.courtFree && cell.fitsFree > 0;
}

/**
 * **Whether a tap opens the cell's sheet** — every cell but one earlier today: a dead cell's sheet
 * says *nobody who fits is free then*, a courtless one that every game needs a court, and either
 * may still list a game already happening there.
 */
export function opensSheet(cell: PostingCell): boolean {
  return !cell.past;
}

/** The pick is in this cell — whichever of its courts it picked. */
export function isPicked(cell: CellAt, pick: PostPick | undefined): boolean {
  return pick !== undefined && pick.day === cell.day && pick.range === cell.range;
}

// ---------------------------------------------------------------------------
// A cell's sheet
// ---------------------------------------------------------------------------

/**
 * **Whether a free court may be picked** — only where somebody who fits is free at its hour: *nobody
 * who fits free: cannot be picked* (§9.1 step 5). The sheet lists every free court hour of the range
 * whatever the fits, so a dead cell's courts and a *0 free* row are drawn and shut.
 */
export function courtPickable(court: Pick<FreeCourt, 'fitsFree'>): boolean {
  return court.fitsFree > 0;
}

/** This court hour is the pick. */
export function isPickedCourt(
  court: Pick<FreeCourt, 'club' | 'startsAt'>,
  pick: PostPick | undefined,
): boolean {
  return pick !== undefined && pick.clubId === court.club.id && pick.startsAt === court.startsAt;
}

/**
 * **What a yes on a post already happening is said on** — a *Challenge*, as the post is dealt: a free
 * vote while more than its seat is open, and on its last seat the booking itself, as a card's *Book it
 * now* is — so the fill holds it ten seconds behind *Undo* (`waitsForUndo`). The sheet carries no
 * court state, so it is read off the seats, the details' own rule.
 */
export function yesOnPost(post: Pick<PostStillFilling, 'proposalId' | 'openSeats'>): YesOn {
  return {
    proposalId: post.proposalId,
    type: 'CHALLENGE',
    court: post.openSeats === 1 ? 'BOOK_IT_NOW' : 'COURT_AVAILABLE',
  };
}

/** The most a cell counts before it says *5+* (A5.2). */
export const FITS_CAP = 5;

/** **The number in a cell** — the count up to the cap, the cap with a plus past it; none when dead. */
export function fitsShown(
  cell: Pick<PostingCell, 'fitsFree'>,
): { readonly count: number; readonly more: boolean } | undefined {
  if (cell.fitsFree <= 0) return undefined;
  return cell.fitsFree > FITS_CAP
    ? { count: FITS_CAP, more: true }
    : { count: cell.fitsFree, more: false };
}

/** The cell a column holds for a range — absent where the read left it out. */
export function cellIn(day: PostingDay, range: DayRange): PostingCell | undefined {
  return day.cells.find((cell) => cell.range === range);
}

// ---------------------------------------------------------------------------
// The level range
// ---------------------------------------------------------------------------

/** One step of a stepper, in hundredths: 0,05. */
const STEP = 5;

/**
 * **The narrowed bounds**, in whole hundredths — each absent while it stands at the engine's own.
 */
export interface Narrowing {
  readonly low?: number;
  readonly high?: number;
}

export const UNNARROWED: Narrowing = {};

export type Bound = 'low' | 'high';
export type Way = 'down' | 'up';

/**
 * What a key does: the bound **moved**; **bounced** — pushed past the engine's own, which *You can
 * narrow it, not widen it* says; or **shut** — it would pass the other bound.
 */
export type LevelStep =
  | { readonly kind: 'moved'; readonly narrowing: Narrowing }
  | { readonly kind: 'bounced' }
  | { readonly kind: 'shut' };

const hundredths = (value: number) => Math.round(value * 100);

/** One bound set — or dropped, back to the engine's. */
function withBound(narrowing: Narrowing, bound: Bound, value: number | undefined): Narrowing {
  const { [bound]: _was, ...rest } = narrowing;
  return value === undefined ? rest : { ...rest, [bound]: value };
}

/** The two bounds the steppers show. */
export function narrowedBounds(engine: LevelRange, narrowing: Narrowing): LevelRange {
  return {
    low: (narrowing.low ?? hundredths(engine.low)) / 100,
    high: (narrowing.high ?? hundredths(engine.high)) / 100,
  };
}

/**
 * **A key pressed** — `up` on the lower bound and `down` on the upper narrow; the others widen, back
 * as far as the engine's bound and no further: a bound already there **bounces**.
 */
export function stepBound(
  engine: LevelRange,
  narrowing: Narrowing,
  bound: Bound,
  way: Way,
): LevelStep {
  const edge = hundredths(engine[bound]);
  const at = narrowing[bound] ?? edge;
  const next = at + (way === 'up' ? STEP : -STEP);
  const outward = (bound === 'low') === (way === 'down');
  if (outward) {
    if (narrowing[bound] === undefined) return { kind: 'bounced' };
    const reached = bound === 'low' ? next <= edge : next >= edge;
    return { kind: 'moved', narrowing: withBound(narrowing, bound, reached ? undefined : next) };
  }
  const bounds = narrowedBounds(engine, narrowing);
  const other = hundredths(bound === 'low' ? bounds.high : bounds.low);
  const passes = bound === 'low' ? next > other : next < other;
  return passes
    ? { kind: 'shut' }
    : { kind: 'moved', narrowing: withBound(narrowing, bound, next) };
}

/** **What the ask sends** — each bound only once it has been narrowed; the engine's own otherwise. */
export function levelAsk(narrowing: Narrowing): Pick<PostingAsk, 'levelLow' | 'levelHigh'> {
  return {
    ...(narrowing.low === undefined ? {} : { levelLow: narrowing.low / 100 }),
    ...(narrowing.high === undefined ? {} : { levelHigh: narrowing.high / 100 }),
  };
}

// ---------------------------------------------------------------------------
// Who
// ---------------------------------------------------------------------------

/** **Who a game may be for** — *Mixed pairs* only in doubles: a side of one is not a pair. */
export function whoOffered(doubles: boolean): readonly Who[] {
  return doubles ? WHO_ORDER : WHO_ORDER.filter((who) => who !== 'MIXED_PAIRS');
}

/** The draft's *Who* as the sport offers it — *Mixed pairs* read as *Anyone* one a side. */
export function draftWho(draft: Pick<PostDraft, 'who'>, doubles: boolean): Who {
  return doubles || draft.who !== 'MIXED_PAIRS' ? draft.who : 'ANYONE';
}

/**
 * **The draft's sport** — the one chosen; until then the page's, while the player may post in it;
 * else the first they may. The page's sport alone when there is none to post in, which the page
 * never mounts the screen for.
 */
export function draftSport(
  draft: Pick<PostDraft, 'sport'>,
  sports: readonly Sport[],
  opening: Sport,
): Sport {
  if (draft.sport !== undefined) return draft.sport;
  return sports.includes(opening) ? opening : (sports[0] ?? opening);
}

// ---------------------------------------------------------------------------
// The draft
// ---------------------------------------------------------------------------

/**
 * **The hour and court in the post** — picked on a cell's sheet; one hour, one court. The player's
 * choice and nothing the server said about it: the club's name and the share are the slot's read,
 * looked up again wherever they are drawn.
 */
export interface PostPick extends CellAt {
  readonly week: PostingWeek;
  readonly clubId: string;
  readonly startsAt: string;
}

/**
 * **What the controls hold** while the player stays in the group (A5). The sport and the kind are
 * absent until chosen — the page's sport and the player's intent stand in — so a default that
 * arrives with a read is never frozen into the draft before the player has said anything.
 */
export interface PostDraft {
  readonly sport?: Sport;
  readonly kind?: GameKind;
  readonly who: Who;
  readonly narrowing: Narrowing;
  readonly week: PostingWeek;
  readonly pick?: PostPick;
}

export const NEW_DRAFT: PostDraft = { who: 'ANYONE', narrowing: UNNARROWED, week: 1 };

/**
 * **A sport chosen** — the level range back to the engine's and the pick gone (A5.1), and *Mixed
 * pairs* back to *Anyone* in a sport played one a side.
 */
export function withSport(draft: PostDraft, sport: Sport, doubles: boolean): PostDraft {
  return {
    ...draft,
    sport,
    who: draftWho(draft, doubles),
    narrowing: UNNARROWED,
    pick: undefined,
  };
}

/**
 * **A kind chosen** — the level range re-seeded, because the engine's window is the kind's (Q78): a
 * bound narrowed inside one kind's window may lie outside the other's. The pick stays: the court is
 * still free, and the grid says whether anybody fits it now.
 */
export function withKind(draft: PostDraft, kind: GameKind): PostDraft {
  return { ...draft, kind, narrowing: UNNARROWED };
}

export function withWho(draft: PostDraft, who: Who): PostDraft {
  return { ...draft, who };
}

export function withNarrowing(draft: PostDraft, narrowing: Narrowing): PostDraft {
  return { ...draft, narrowing };
}

/** The week shown — the pick stays wherever it is. */
export function withWeek(draft: PostDraft, week: PostingWeek): PostDraft {
  return { ...draft, week };
}

/** A new pick replaces the old (A5.3). */
export function withPick(draft: PostDraft, pick: PostPick): PostDraft {
  return { ...draft, pick };
}

/** *Remove this pick*. */
export function withoutPick(draft: PostDraft): PostDraft {
  return { ...draft, pick: undefined };
}
