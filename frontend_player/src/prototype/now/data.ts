/**
 * THROWAWAY PROTOTYPE — issue #11. Not production. Deleted with the branch.
 *
 * Six enrolled-match contexts, copied verbatim from the v37 prototype's `ST` table
 * (`docs/specs/now/prototype-v37/rakietaPlayerPrototype.html`, lines 3557–3844) so the
 * card is measured against real strings, not lorem. Real copy is the point: `heldSoft`
 * has five lines and a Court value that wraps to two, `cancelledClub`'s Group value is
 * two words, and that spread is what question 4 asks about.
 */

export type Tone = 'good' | 'watch' | 'time' | 'ended' | 'idle' | 'bad';
export type SeatSym = 'me' | 'g' | 'x' | null;

export interface ProtoState {
  readonly key: string;
  readonly tag: string;
  readonly tone: Tone;
  readonly startTime: string;
  readonly whenLabel: string;
  readonly clubName: string;
  readonly courtLabel: string;
  readonly durationMin: number;
  readonly sport: 'padel' | 'tennis' | 'squash' | 'badminton';
  readonly format: string;
  readonly seats: readonly SeatSym[];
  readonly filled: number;
  readonly capacity: number;
  readonly court: string;
  readonly group: string;
  readonly alert?: { readonly text: string; readonly bold: string };
  readonly lines: readonly (readonly [0 | 1, string])[];
  readonly post?: boolean;
}

export const STATES: readonly ProtoState[] = [
  {
    key: 'heldSoft',
    tag: 'Court held',
    tone: 'watch',
    startTime: '18:30',
    whenLabel: 'Today · 18:30',
    clubName: 'Mondo Sport',
    courtLabel: 'Court 2 · Mondo',
    durationMin: 90,
    sport: 'padel',
    format: 'Doubles',
    seats: ['me', 'x', null, null],
    filled: 2,
    capacity: 4,
    court: 'Held · Indoor panoramic — held until 12h before play',
    group: '2 of 4 seats paid',
    lines: [
      [1, 'You paid 34,00 zł'],
      [1, 'A court is being held, but this is not yet a firm booking'],
      [
        0,
        'Two paid seats hold a court while there is plenty of time to sell it. From 24 hours before play we need a third, or it goes back',
      ],
      [
        0,
        'If it goes back nothing you paid is affected, and it returns the moment another player pays',
      ],
      [0, 'Leaving now returns everything, in minutes'],
    ],
  },
  {
    key: 'replacement',
    tag: 'Replacement pending',
    tone: 'watch',
    startTime: '20:00',
    whenLabel: 'Sat · 20:00',
    clubName: 'Hala Wisła',
    courtLabel: 'Court 5 · Wisła',
    durationMin: 60,
    sport: 'tennis',
    format: 'Doubles',
    seats: ['me', 'x', 'x', null],
    filled: 3,
    capacity: 4,
    court: '136,00 zł settled to the club',
    group: '3 of 4 · the seat stays funded',
    alert: {
      text: 'Kuba left after the commitment deadline. We are looking for a replacement. ',
      bold: 'Your payment will not change.',
    },
    lines: [
      [1, 'You paid 34,00 zł — nothing about your booking changes'],
      [0, 'Their payment stays on the seat, so the court is safe'],
      [0, 'The seat is offered at the normal 34,00 zł to compatible players'],
      [0, 'They are refunded in full if somebody pays it'],
    ],
  },
  {
    key: 'waitlisted',
    tag: 'On standby',
    tone: 'idle',
    startTime: '07:15',
    whenLabel: 'Sun · 07:15',
    clubName: 'Squash Zone',
    courtLabel: 'Court 1 · Zone',
    durationMin: 45,
    sport: 'squash',
    format: 'Singles',
    seats: ['x', 'x'],
    filled: 2,
    capacity: 2,
    court: 'Fully paid by four other players',
    group: '4 of 4 · you are 2nd on the standby list',
    lines: [
      [1, 'You joined the standby list · 0,00 zł'],
      [0, 'If a seat frees the top candidates are told at the same moment'],
      [0, 'Ten minutes to accept, five to pay, then it moves on'],
      [0, 'Ignoring it costs nothing and you keep your place'],
    ],
  },
  {
    key: 'cancelledClub',
    tag: 'Cancelled',
    tone: 'ended',
    startTime: '09:00',
    whenLabel: 'Today · 09:00',
    clubName: 'Mondo Sport',
    courtLabel: 'Court 4 · Mondo',
    durationMin: 90,
    sport: 'padel',
    format: 'Doubles',
    seats: ['me', 'x', 'x', 'x'],
    filled: 4,
    capacity: 4,
    court: 'Cancelled by Mondo Sport',
    group: 'everybody refunded',
    lines: [
      [1, 'The club cancelled at 08:12 — standing water on the court'],
      [1, 'Everybody is refunded in full, including anybody who had already left'],
      [1, 'A Rescue payment, if one had been made, is refunded too'],
      [0, 'Nobody’s reliability is touched. Alternatives are suggested below'],
    ],
  },
  {
    key: 'ready',
    tag: 'Ready to play',
    tone: 'good',
    startTime: '19:45',
    whenLabel: 'Today · 19:45',
    clubName: 'Mondo Sport',
    courtLabel: 'Court 2 · Mondo',
    durationMin: 90,
    sport: 'padel',
    format: 'Doubles',
    seats: ['me', 'x', 'x', 'x'],
    filled: 4,
    capacity: 4,
    court: 'Court 2 · Mondo',
    group: '4 of 4 · everybody expected',
    lines: [
      [1, 'Everybody has paid and the court is booked'],
      [1, 'Your door code is live 15 minutes before play'],
    ],
  },
  {
    key: 'completed',
    tag: 'Completed',
    tone: 'good',
    startTime: '18:30',
    whenLabel: 'Yesterday · 18:30',
    clubName: 'Hala Wisła',
    courtLabel: 'Court 5 · Wisła',
    durationMin: 60,
    sport: 'tennis',
    format: 'Doubles',
    seats: ['me', 'x', 'x', 'x'],
    filled: 4,
    capacity: 4,
    court: 'Settled',
    group: '4 of 4 played',
    post: true,
    lines: [
      [1, 'Result recorded and confirmed'],
      [1, 'Everybody’s rating has moved'],
    ],
  },
];

/** The recommendation feed below the strip. Enough to make the screen read as Now. */
export const FEED = [
  {
    when: 'Today · 21:00',
    badge: 'Promotion',
    club: 'Mondo Sport',
    travel: 12,
    sport: 'padel' as const,
    format: 'Doubles',
    counts: true,
    cardOff: 'card −all',
    seats: ['x', 'x', null, null] as SeatSym[],
    filled: 2,
    capacity: 4,
    fit: 91,
    emphatic: true,
    stateTag: 'Forming',
    stateTone: 'idle' as Tone,
    strike: '34,00 zł',
    payable: '0,00 zł',
  },
  {
    when: 'Sat · 10:00',
    club: 'Squash Zone',
    travel: 21,
    sport: 'squash' as const,
    format: 'Singles',
    counts: false,
    seats: ['x', null] as SeatSym[],
    filled: 1,
    capacity: 2,
    fit: 74,
    emphatic: false,
    stateTag: 'Court held',
    stateTone: 'watch' as Tone,
    payable: '29,00 zł',
  },
];

/**
 * Default knob positions. Lives here rather than in the screen so that editing it forces
 * Metro to reload the whole tree — Fast Refresh preserves `useState` across a component
 * edit, which makes a default unchangeable without a full reload.
 */
export const INITIAL_KNOBS = {
  width: 320 as 'device' | 320 | 375 | 393 | 430,
  strip: 'bleed' as 'bleed' | 'ratio' | 'inset',
  overlay: 'off' as 'off' | 'touch',
  fixContrast: false,
};
