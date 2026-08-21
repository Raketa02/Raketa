/**
 * THROWAWAY PROTOTYPE — issue #24. Not production.
 *
 * One evening, four people, two sports. The fixture exists so the four screens are
 * measured against a real disagreement rather than lorem: Kuba proposes 6-4 3-6 6-2 and
 * Marta's side thinks the third set was 6-4, which is one digit apart and is exactly the
 * kind of disagreement this flow has to survive without a chat.
 *
 * The score SHAPES come from `deltas/result-confirmation.md` §5: padel and tennis in sets
 * and games, squash and badminton in games and points, validated permissively — the app
 * knows the shape and declines the obviously impossible, and never enforces the rulebook.
 */

export type SeatSym = 'me' | 'g' | 'x' | null;

export type SportKey = 'padel' | 'tennis' | 'squash' | 'badminton';

/** A leg is one set (padel/tennis) or one game (squash/badminton): two numbers. */
export type Leg = readonly [number | null, number | null];

export interface Shape {
  /** What one row of the grid is called, singular. */
  readonly leg: string;
  /** How many rows the grid offers. `3.1` fixes no format, so this is the common one. */
  readonly legs: number;
  /** The pad's normal range. Beyond it the `+` key keeps counting — permissive, per §5. */
  readonly padTo: number;
  /** Rendered under the grid as the thing the app knows about this sport. */
  readonly note: string;
}

export const SHAPE: Record<SportKey, Shape> = {
  padel: { leg: 'Set', legs: 3, padTo: 7, note: 'Sets and games' },
  tennis: { leg: 'Set', legs: 3, padTo: 7, note: 'Sets and games' },
  squash: { leg: 'Game', legs: 5, padTo: 11, note: 'Games and points' },
  badminton: { leg: 'Game', legs: 3, padTo: 21, note: 'Games and points' },
};

export interface Side {
  /** How the side is named on every screen that shows a score. */
  readonly label: string;
  readonly mine: boolean;
}

export interface Fixture {
  readonly sport: SportKey;
  readonly format: string;
  readonly startTime: string;
  readonly whenLabel: string;
  readonly clubName: string;
  readonly courtLabel: string;
  readonly durationMin: number;
  readonly seats: readonly SeatSym[];
  readonly capacity: number;
  /** The side the viewer plays for is always `sides[0]` — the grid's top row is yours. */
  readonly sides: readonly [Side, Side];
  /** Who typed the live proposal, and what it says. */
  readonly proposer: string;
  readonly proposed: readonly Leg[];
  /** What the opposing side would type instead — the counter's pre-load. */
  readonly counter: readonly Leg[];
  /** Absolute times, because a countdown alone never says WHEN. */
  readonly enteredAt: string;
  readonly standsAt: string;
  readonly standsIn: string;
  /** The entry deadline, shown before anybody has proposed anything. */
  readonly entryDeadline: string;
}

export const FIXTURES: Record<'padel' | 'squash', Fixture> = {
  padel: {
    sport: 'padel',
    format: 'Doubles',
    startTime: '18:30',
    whenLabel: 'Yesterday · 18:30',
    clubName: 'Mondo Sport',
    courtLabel: 'Court 2 · Mondo',
    durationMin: 90,
    seats: ['me', 'x', 'x', 'x'],
    capacity: 4,
    sides: [
      { label: 'You & Marta', mine: true },
      { label: 'Kuba & Ada', mine: false },
    ],
    proposer: 'Kuba',
    // Read as YOUR games first, always: the grid's top row is the viewer's side.
    proposed: [
      [4, 6],
      [6, 3],
      [2, 6],
    ],
    counter: [
      [4, 6],
      [6, 3],
      [4, 6],
    ],
    enteredAt: 'Yesterday 20:12',
    standsAt: 'Sunday 20:12',
    standsIn: '19 h',
    entryDeadline: 'Sunday 20:00',
  },
  squash: {
    sport: 'squash',
    format: 'Singles',
    startTime: '07:15',
    whenLabel: 'Today · 07:15',
    clubName: 'Hala Wisła',
    courtLabel: 'Court 5 · Wisła',
    durationMin: 45,
    seats: ['me', 'x'],
    capacity: 2,
    sides: [
      { label: 'You', mine: true },
      { label: 'Piotr', mine: false },
    ],
    proposer: 'Piotr',
    proposed: [
      [11, 9],
      [8, 11],
      [11, 13],
      [6, 11],
      [null, null],
    ],
    counter: [
      [11, 9],
      [8, 11],
      [11, 13],
      [9, 11],
      [null, null],
    ],
    enteredAt: 'Today 08:31',
    standsAt: 'Tomorrow 08:31',
    standsIn: '22 h',
    entryDeadline: 'Tomorrow 08:00',
  },
};

/** `6-4 3-6 6-2` — the one-line form the card and the prompt both need. */
export function inlineScore(legs: readonly Leg[]): string {
  return legs
    .filter(([a, b]) => a !== null && b !== null)
    .map(([a, b]) => `${a}-${b}`)
    .join(' ');
}

/**
 * Permissive validation, per §5: decline the obviously impossible, never the rulebook.
 * A tie is not a result; an empty grid is not a result; a leg half-filled is a typo.
 * 7-6, 6-0, 15-13 and a timed 3-2 all pass, because they all happen.
 */
export function refuse(legs: readonly Leg[]): string | null {
  const played = legs.filter(([a, b]) => a !== null || b !== null);
  if (played.length === 0) return 'Type the first set to continue';
  if (played.some(([a, b]) => a === null || b === null)) return 'One side of a set is missing';
  const mine = played.filter(([a, b]) => (a as number) > (b as number)).length;
  const theirs = played.length - mine;
  if (played.some(([a, b]) => a === b)) return 'A set cannot end level';
  if (mine === theirs) return 'This score has no winner — add the deciding set';
  return null;
}
