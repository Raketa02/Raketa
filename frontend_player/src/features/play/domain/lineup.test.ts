import { theme } from '@/shared/ui/theme';

import {
  SEAT_PLACES,
  changingMode,
  changingSport,
  courtHalfOf,
  leavingFindAGame,
  lineupStanding,
  sameOrigin,
  seatIsClearable,
  seatIsLocked,
  seatPlaces,
  tapSeat,
  withheldSeats,
  type BuildSeat,
  type Lineup,
  type LineupInPlay,
  type OriginSearch,
  type PlayOrigin,
} from './lineup';

const TUESDAY_EVENING = { day: 2, part: 'evening' } as const;
const SATURDAY_MORNING = { day: 6, part: 'morning' } as const;

const ORIGIN: PlayOrigin = {
  sport: 'padel',
  mode: 'COMPETITIVE',
  week: [TUESDAY_EVENING, SATURDAY_MORNING],
};

const SEARCH: OriginSearch = { searchId: 'search-1', origin: ORIGIN };

const LINEUP: Lineup = { originSearchId: 'search-1', seats: ['player-a', 'player-b'] };

/** A player on the builder with two people seated, still searching for what they searched for. */
const IN_PLAY: LineupInPlay = { lineup: LINEUP, originSearch: SEARCH, now: ORIGIN };

describe('an origin', () => {
  it('is three facts, and the week compares as a set', () => {
    expect(sameOrigin(ORIGIN, { ...ORIGIN, week: [SATURDAY_MORNING, TUESDAY_EVENING] })).toBe(true);
  });

  it('differs on the sport, on the mode, and on the week', () => {
    expect(sameOrigin(ORIGIN, { ...ORIGIN, sport: 'tennis' })).toBe(false);
    expect(sameOrigin(ORIGIN, { ...ORIGIN, mode: 'FOR_FUN' })).toBe(false);
    expect(sameOrigin(ORIGIN, { ...ORIGIN, week: [TUESDAY_EVENING] })).toBe(false);
  });
});

describe('where a line-up stands', () => {
  it('is current while the origin search is what the player is still searching for', () => {
    expect(lineupStanding(IN_PLAY)).toEqual({ kind: 'current' });
  });

  it('is nothing at all when no seat has been filled', () => {
    expect(lineupStanding({ ...IN_PLAY, lineup: undefined })).toEqual({ kind: 'none' });
    expect(
      lineupStanding({ ...IN_PLAY, lineup: { originSearchId: 'search-1', seats: [] } }),
    ).toEqual({ kind: 'none' });
  });

  it('AC-8: is orphaned by a change of sport', () => {
    expect(lineupStanding({ ...IN_PLAY, now: { ...ORIGIN, sport: 'tennis' } })).toEqual({
      kind: 'orphaned',
    });
  });

  it('is orphaned by a change of mode — the origin is not sport alone', () => {
    expect(lineupStanding({ ...IN_PLAY, now: { ...ORIGIN, mode: 'FOR_FUN' } })).toEqual({
      kind: 'orphaned',
    });
  });

  it('is orphaned by an edited week, which the search carried as availability_override', () => {
    expect(lineupStanding({ ...IN_PLAY, now: { ...ORIGIN, week: [TUESDAY_EVENING] } })).toEqual({
      kind: 'orphaned',
    });
  });

  it('AC-70: an abandoned search cannot reach the line-up you are looking at', () => {
    // The abandoned run minted its own id and wrote its rows under its own key. Reading the
    // line-up's origin reads *its* search, so the other one is not a case to handle — it is
    // an entry nothing looks at.
    const abandoned: OriginSearch = {
      searchId: 'search-2',
      origin: { ...ORIGIN, sport: 'squash' },
    };

    expect(lineupStanding({ ...IN_PLAY, originSearch: abandoned })).toEqual({ kind: 'unreadable' });
  });

  it('says unreadable rather than orphaned when the origin search is not held', () => {
    expect(lineupStanding({ ...IN_PLAY, originSearch: undefined })).toEqual({ kind: 'unreadable' });
  });
});

describe('the guard, and its three callers', () => {
  it('lets an act through when there is no line-up to lose', () => {
    expect(changingSport({ ...IN_PLAY, lineup: undefined }, 'tennis')).toEqual({ kind: 'go' });
  });

  it('lets an act through when it changes nothing', () => {
    // Re-selecting the sport already selected raises no modal — that is what keeps the
    // confirmation worth reading.
    expect(changingSport(IN_PLAY, 'padel')).toEqual({ kind: 'go' });
    expect(changingMode(IN_PLAY, 'COMPETITIVE')).toEqual({ kind: 'go' });
    expect(leavingFindAGame(IN_PLAY)).toEqual({ kind: 'go' });
  });

  it('asks first on all three triggers, and says how many people it is about', () => {
    expect(changingSport(IN_PLAY, 'tennis')).toEqual({ kind: 'ask', seated: 2 });
    expect(changingMode(IN_PLAY, 'FOR_FUN')).toEqual({ kind: 'ask', seated: 2 });
    expect(leavingFindAGame({ ...IN_PLAY, now: { ...ORIGIN, week: [TUESDAY_EVENING] } })).toEqual({
      kind: 'ask',
      seated: 2,
    });
  });

  it('is one guard: the three callers differ only in which field of the origin moves', () => {
    expect(changingSport(IN_PLAY, 'tennis')).toEqual(
      leavingFindAGame({ ...IN_PLAY, now: { ...ORIGIN, sport: 'tennis' } }),
    );
    expect(changingMode(IN_PLAY, 'FOR_FUN')).toEqual(
      leavingFindAGame({ ...IN_PLAY, now: { ...ORIGIN, mode: 'FOR_FUN' } }),
    );
  });

  it('asks rather than destroying silently when the origin search cannot be read', () => {
    // Going ahead here would be §G6 bug #6 exactly — a line-up destroyed with no confirmation.
    // Which of two causes destroyed it is not something the player can see.
    expect(changingSport({ ...IN_PLAY, originSearch: undefined }, 'tennis')).toEqual({
      kind: 'ask',
      seated: 2,
    });
  });
});

describe('a seat whose player the live gates no longer admit', () => {
  it('is a set difference against the rows the read-back still holds', () => {
    expect(withheldSeats(LINEUP, ['player-b'])).toEqual(['player-a']);
  });

  it('marks nothing while every seated player is still live', () => {
    expect(withheldSeats(LINEUP, ['player-a', 'player-b', 'somebody-else'])).toEqual([]);
  });

  it('marks nothing at all until there has been a read-back', () => {
    // A withheld row carries no id, so the only thing a client can know is which rows are
    // still live. With no read-back held there are none of those — and reading that as
    // "everybody is gone" would mark a whole court on a cold cache.
    expect(withheldSeats(LINEUP, undefined)).toEqual([]);
  });

  it('leaves the line-up exactly as it was — the mark is derived, never stored', () => {
    // A stored mark is a third thing that can be stale about staleness, and it would outlive
    // the read-back that justified it.
    withheldSeats(LINEUP, []);

    expect(LINEUP.seats).toEqual(['player-a', 'player-b']);
  });

  it('keeps the marked player seated, so the forecast is still asked about four', () => {
    // Dropping them would make the number silently disagree with the court in front of the
    // player, and would force a second cause for *provisional*.
    const marked = withheldSeats(LINEUP, ['player-b']);

    expect(LINEUP.seats).toContain(marked[0]);
    expect(lineupStanding({ lineup: LINEUP, originSearch: SEARCH, now: ORIGIN })).toEqual({
      kind: 'current',
    });
  });

  it('has nothing to mark on a line-up nobody has started', () => {
    expect(withheldSeats(undefined, ['player-a'])).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// The court's three: H-25's sides, the locked seats, and the swap truth table
// ---------------------------------------------------------------------------

/** A doubles court as it starts: you, and three seats nobody has filled. */
const EMPTY_DOUBLES: readonly BuildSeat[] = [
  { kind: 'you' },
  { kind: 'empty' },
  { kind: 'empty' },
  { kind: 'empty' },
];

const seated = (accepted = false): BuildSeat => ({ kind: 'player', accepted });

/** A full doubles court: you, your partner, and two opponents. */
const FULL_DOUBLES: readonly BuildSeat[] = [{ kind: 'you' }, seated(), seated(), seated()];

/** Nothing held for a trade — the builder as it opens, and after every completed one. */
const RESTING = undefined;

describe("a seat's place", () => {
  it('is a side and a role, read off seat order rather than off the drawing', () => {
    expect(seatPlaces(FULL_DOUBLES)).toEqual([
      'YOUR_SIDE',
      'YOUR_PARTNER',
      'THEIR_SIDE',
      'THEIR_SIDE',
    ]);
  });

  it('has no partner in singles, because your half has one seat in it', () => {
    expect(seatPlaces([{ kind: 'you' }, seated()])).toEqual(['YOUR_SIDE', 'THEIR_SIDE']);
  });

  it('follows you across the net, because a side is the half you are on', () => {
    // The whole point of a swap is *change sides, never seats*. A place read off the index
    // alone would still call the far half theirs after you had moved into it.
    expect(seatPlaces([seated(), seated(), { kind: 'you' }, seated()])).toEqual([
      'THEIR_SIDE',
      'THEIR_SIDE',
      'YOUR_SIDE',
      'YOUR_PARTNER',
    ]);
  });

  it('cannot be derived from where a seat is drawn, and squash is why (H-25)', () => {
    // Squash has no net: both seats are on the near half of the drawing, and a rule that read
    // the far side off the coordinate would put both players on your side.
    const [near, far] = theme.size.court.seats.squash;
    const half = theme.size.court.space.height / 2;

    expect(near?.[1]).toBeGreaterThan(half);
    expect(far?.[1]).toBeGreaterThanOrEqual(half);
    expect(seatPlaces([{ kind: 'you' }, seated()])).toEqual(['YOUR_SIDE', 'THEIR_SIDE']);
  });
});

describe('which half a place is on', () => {
  it('answers every place in the vocabulary, and your partner is on your half', () => {
    // Per member rather than by counting them: an implementation that inverted the mapping
    // would still produce two of one half and one of the other. Totality itself is the
    // compiler's — the switch has no `default` and declares its return — so what is pinned
    // here is *which* half each place is on.
    expect(SEAT_PLACES.map(courtHalfOf)).toEqual(['yours', 'yours', 'theirs']);
  });

  it('follows you across the net, because it reads a place and never an index', () => {
    // The composition every caller makes, on the one seating where an index would disagree:
    // a swap is *change sides, never seats*, so the half you are standing in is yours.
    expect(seatPlaces([seated(), seated(), { kind: 'you' }, seated()]).map(courtHalfOf)).toEqual([
      'theirs',
      'theirs',
      'yours',
      'yours',
    ]);
  });
});

describe('a locked seat', () => {
  it('is yours, and anybody who has already accepted', () => {
    expect(seatIsLocked({ kind: 'you' })).toBe(true);
    expect(seatIsLocked(seated(true))).toBe(true);
    expect(seatIsLocked(seated())).toBe(false);
    expect(seatIsLocked({ kind: 'empty' })).toBe(false);
  });

  it('may not be emptied, which is why the clear badge is not drawn on one', () => {
    // The only reader `seatIsLocked` has left, and the only refusal on this court: a badge
    // that is never drawn is a refusal nobody can trigger, so nothing has to say no out loud.
    expect(seatIsClearable(seated())).toBe(true);
    expect(seatIsClearable(seated(true))).toBe(false);
    expect(seatIsClearable({ kind: 'you' })).toBe(false);
    expect(seatIsClearable({ kind: 'empty' })).toBe(false);
  });
});

describe('a tap on a seat', () => {
  it('opens the pool on an empty one, held or not — there is nothing in it to trade', () => {
    expect(tapSeat(RESTING, 1, { kind: 'empty' })).toEqual({ kind: 'OPEN_POOL', seat: 1 });
    expect(tapSeat(0, 1, { kind: 'empty' })).toEqual({ kind: 'OPEN_POOL', seat: 1 });
  });

  it('selects, deselects and trades — the whole of what an occupied seat does', () => {
    expect(tapSeat(RESTING, 1, seated())).toEqual({ kind: 'SELECT', seat: 1 });
    expect(tapSeat(1, 1, seated())).toEqual({ kind: 'DESELECT' });
    expect(tapSeat(1, 3, seated())).toEqual({ kind: 'SWAP', from: 1, to: 3 });
  });

  it('never opens the pool against somebody, because a tap no longer replaces anybody', () => {
    // The row the toggle's removal deleted. Replacing is the clear badge and then the hole it
    // leaves, which is why `seatIsClearable` and not this function is what gates a swap out.
    expect(tapSeat(RESTING, 2, seated())).toEqual({ kind: 'SELECT', seat: 2 });
  });

  it('lets a locked seat change sides, which is the whole of what a swap is for', () => {
    // *They can change sides, never seats.* Both refusals were the replacement's, and there is
    // no replacement on a tap left to refuse.
    expect(tapSeat(RESTING, 0, { kind: 'you' })).toEqual({ kind: 'SELECT', seat: 0 });
    expect(tapSeat(0, 3, seated(true))).toEqual({ kind: 'SWAP', from: 0, to: 3 });
  });

  it('leaves an untouched court untouched — every outcome is a decision, never a write', () => {
    tapSeat(RESTING, 1, EMPTY_DOUBLES[1] ?? { kind: 'empty' });

    expect(EMPTY_DOUBLES[1]).toEqual({ kind: 'empty' });
  });
});
