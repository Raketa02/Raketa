/**
 * **Every fixed word *Post a game* says** — the controls, the grid, its legend, a cell's sheet and
 * the button ([#558](https://github.com/Rakieta02/Rakieta/issues/558); the screens A5; mocks 15–35).
 * Copy is code; nothing is inlined in a component.
 *
 * Import-free but for types, so a screen can read it at module load; the sentences composed from a
 * value are `postingPresentation.ts`. Taken from the mocks and the screens' text, with their names,
 * prices and dates read as mock data — none of it is here.
 */

import type { CellFill } from '../domain/posting';
import type { DayRange, GameKind, Who } from '../domain/vocabulary';

/** A post with nothing saved to pay with — before the press, and as the server's refusal. */
const PAYMENT_FIRST = 'A post needs a saved way to pay first — nothing is charged until it fills.';

export const POSTING_COPY = {
  title: 'Post a game',
  sport: 'Sport',
  kind: 'Kind',
  who: 'Who',
  level: 'Level',
  levelAside: 'narrow it, not widen it',
  when: 'When',
  /** The kind's two segments (mock 17) — *For fun* is a friendly. */
  kinds: {
    competitive: 'Competitive',
    forFun: 'For fun · friendly',
  } satisfies Readonly<Record<GameKind, string>>,
  kindsSpoken: {
    competitive: 'Competitive',
    forFun: 'For fun, a friendly',
  } satisfies Readonly<Record<GameKind, string>>,
  /** Who the game is for (mock 18). */
  whoLabels: {
    ANYONE: 'Anyone',
    MEN: 'Men',
    WOMEN: 'Women',
    MIXED_PAIRS: 'Mixed pairs',
  } satisfies Readonly<Record<Who, string>>,
  /** The four stepper keys, each named for what it does. */
  levelKeys: {
    lowDown: 'Lower the lowest level',
    lowUp: 'Raise the lowest level',
    highDown: 'Lower the highest level',
    highUp: 'Raise the highest level',
  },
  /** What a bound pushed past the engine's own says (A5.1). */
  bounce: 'You can narrow it, not widen it',
  /** The steppers before the grid has said where the engine's window is. */
  levelPending: '–',
  weeks: { 1: 'This week', 2: 'Next week' },
  earlierWeek: 'Show this week',
  laterWeek: 'Show next week',
  today: 'Today',
  ranges: {
    MORNING: 'Morning',
    AFTERNOON: 'Afternoon',
    EVENING: 'Evening',
  } satisfies Readonly<Record<DayRange, string>>,
  /** A range's hours, from and to (Q71: Morning 07–12, Afternoon 12–17, Evening 17–23). */
  rangeHours: {
    MORNING: ['07:00', '12:00'],
    AFTERNOON: ['12:00', '17:00'],
    EVENING: ['17:00', '23:00'],
  } satisfies Readonly<Record<DayRange, readonly [string, string]>>,
  rangeInLine: {
    MORNING: 'morning',
    AFTERNOON: 'afternoon',
    EVENING: 'evening',
  } satisfies Readonly<Record<DayRange, string>>,
  /** Today's ranges in a sheet's title — *This evening*, never *Today evening*. */
  thisRange: {
    MORNING: 'This morning',
    AFTERNOON: 'This afternoon',
    EVENING: 'This evening',
  } satisfies Readonly<Record<DayRange, string>>,
  /** What each look says to a listener — the number and the flags are said beside it. */
  fillSpoken: {
    dead: 'nobody who fits is free',
    few: 'no court free',
    enough: 'a full game free, no court',
    thin: 'a court free, may not fill',
    hot: 'a court free and a full game',
  } satisfies Readonly<Record<CellFill, string>>,
  happeningSpoken: 'a game already happening here',
  outsideSpoken: 'outside your hours',
  pastSpoken: 'earlier today',
  pickedSpoken: 'your pick',
  cellHint: 'Opens what is free then',
  reading: 'Reading when your best fits are free',
  /** The screen while the group and the phone are read. */
  opening: 'Opening Post a game',
  /** Between a range's two hours, spoken — *07:00 to 12:00*. */
  hoursTo: 'to',
  /** The legend (mock 20), its red-dot line as A5.2 changed it. */
  legend: {
    open: 'How to read the map',
    title: 'How to read the map',
    close: 'Close how to read the map',
    brighter:
      'Brighter means more of the group is free for this game and a club has a court. The brightest slots are the ones to pick.',
    count:
      'How many of your best fits — matching the kind, who and level you chose — are free then, together with you. Only players whose availability overlaps are counted, and shown.',
    court:
      'A free court at the group’s clubs. Only these hours can be picked: tap one, pick the court. Posting is your yes, and deals it to your best fits as a Challenge.',
    happening:
      'A game already happening there — posted, or a booked game missing a player. Tap to see it.',
    outside: 'Dimmed: outside your weekly hours.',
    pick: 'Pick one hour — fewer fits than seats says so: “only 2 fit · may not fill”.',
    /** The count badge's sample figure, as the mock draws it. */
    sampleCount: '3',
  },
  post: 'Post — you’re In',
  paymentFirst: PAYMENT_FIRST,
  posting: 'Posting…',
  /** Under the button until a court is picked (mock 15). */
  pickFirst: 'Pick an hour with a court on the map first.',
  ifItFills: 'if it fills',
  each: 'each',
  /** A post the server refused — under the button, in the helper's place (A5.4). */
  refused: {
    payment_method_required: PAYMENT_FIRST,
    live_posts_exhausted:
      'You already have 2 posts live — withdraw one in You’re in to post again.',
    you_play_then: 'You already have a game at that hour.',
    nobody_fits_then: 'None of your best fits is free then any more — pick another hour.',
    court_hour_not_for_sale: 'That court isn’t for sale any more — pick another.',
    who_leaves_you_out: 'This game wouldn’t include you — choose who it’s for again.',
    not_rated_in_the_sport: 'Get rated in this sport to post in it.',
    level_range_too_wide: 'That level range is wider than the engine allows.',
    level_range_inverted: 'The lowest level is above the highest.',
    mixed_pairs_only_in_doubles: 'Mixed pairs is for doubles only.',
    pool_not_found: 'This group isn’t open to you any more.',
  } as Readonly<Record<string, string>>,
  /** The grid's read refused for the controls themselves — said in the grid's place. */
  gridRefused: {
    who_leaves_you_out: 'A game for them wouldn’t include you — choose who it’s for again.',
    not_rated_in_the_sport: 'Get rated in this sport to post in it.',
    pool_not_found: 'This group isn’t open to you any more.',
  } as Readonly<Record<string, string>>,
  sheet: {
    close: 'Close what is free then',
    fitsFree: 'of your best fits free then',
    fitsFreeSpoken: 'of your best fits free',
    mayNotFill: 'may not fill',
    nobody: 'Nobody who fits is free then',
    freeCourts: 'Free courts · home club first',
    noCourt: 'No court is free then — every game needs a court.',
    happening: 'Already happening here',
    remove: 'Remove this pick',
    /** Why a game already happening is listed — every row's, the read lists only these (A5.3). */
    anyLevel: 'any level',
    youAreFree: 'you are free',
    group: 'The group',
    reading: 'Reading what is free then',
    fitHint: 'Opens their record',
    courtHint: 'Picks this court for your post',
  },
} as const;
