/**
 * **Posting a game, the rules the client draws by** — a cell's look, what may be picked, the level
 * steppers that narrow and never widen, who a game may be for, and the draft the controls hold
 * (#558; the screens A5; the mechanics §9.1).
 */

import {
  FITS_CAP,
  NEW_DRAFT,
  UNNARROWED,
  courtPickable,
  draftSport,
  draftWho,
  isPickedCourt,
  yesOnPost,
  cellFill,
  fitsShown,
  isPicked,
  levelAsk,
  narrowedBounds,
  opensSheet,
  pickable,
  stepBound,
  whoOffered,
  withKind,
  withPick,
  withSport,
  withWeek,
  withWho,
  withoutPick,
  type FreeCourt,
  type PostDraft,
  type PostPick,
  type PostingCell,
} from './posting';

function cell(extra: Partial<PostingCell> = {}): PostingCell {
  return {
    day: '2026-10-03',
    range: 'EVENING',
    fitsFree: 5,
    bestStartsAt: '2026-10-03T15:00:00Z',
    courtFree: true,
    fullGame: true,
    outsideYourHours: false,
    past: false,
    happening: false,
    ...extra,
  };
}

const PICK: PostPick = {
  week: 1,
  day: '2026-10-03',
  range: 'EVENING',
  clubId: 'club-1',
  startsAt: '2026-10-03T15:00:00Z',
};

const COURT: FreeCourt = {
  club: { id: 'club-1', name: 'Ogrody 33' },
  homeClub: true,
  startsAt: '2026-10-03T15:00:00Z',
  shareGrosze: 2700,
  bookBy: '2026-10-03T13:00:00Z',
  courts: 2,
  fitsFree: 4,
};

/** The engine's window in the mocks: 2,56–2,86 around a 2,71. */
const ENGINE = { low: 2.56, high: 2.86 };

describe('a cell’s look (the screens A5.2)', () => {
  it('is dead with nobody who fits free, court or no court', () => {
    expect(cellFill(cell({ fitsFree: 0, courtFree: false, fullGame: false }))).toBe('dead');
    expect(cellFill(cell({ fitsFree: 0, courtFree: true, fullGame: false }))).toBe('dead');
  });

  it('is few or enough with no court, by whether a full game’s worth are free', () => {
    expect(cellFill(cell({ fitsFree: 2, courtFree: false, fullGame: false }))).toBe('few');
    expect(cellFill(cell({ fitsFree: 4, courtFree: false, fullGame: true }))).toBe('enough');
  });

  it('is thin or hot with a court, by the same', () => {
    expect(cellFill(cell({ fitsFree: 2, courtFree: true, fullGame: false }))).toBe('thin');
    expect(cellFill(cell({ fitsFree: 5, courtFree: true, fullGame: true }))).toBe('hot');
  });
});

describe('what a tap does', () => {
  it('picks only a cell with a court and somebody who fits, outside your hours too', () => {
    expect(pickable(cell())).toBe(true);
    expect(pickable(cell({ fullGame: false, fitsFree: 1 }))).toBe(true);
    expect(pickable(cell({ outsideYourHours: true }))).toBe(true);
    expect(pickable(cell({ courtFree: false }))).toBe(false);
    expect(pickable(cell({ fitsFree: 0 }))).toBe(false);
    expect(pickable(cell({ past: true }))).toBe(false);
  });

  it('opens the sheet on every cell but one earlier today — the dead and courtless say why', () => {
    expect(opensSheet(cell({ fitsFree: 0, courtFree: false }))).toBe(true);
    expect(opensSheet(cell({ past: true }))).toBe(false);
  });

  it('knows the cell the pick is in, whichever court it picked', () => {
    expect(isPicked(cell(), PICK)).toBe(true);
    expect(isPicked(cell({ range: 'AFTERNOON' }), PICK)).toBe(false);
    expect(isPicked(cell({ day: '2026-10-04' }), PICK)).toBe(false);
    expect(isPicked(cell(), undefined)).toBe(false);
  });
});

describe('a court on the sheet', () => {
  it('is picked only where somebody who fits is free at its hour — nobody, no post (§9.1 step 5)', () => {
    expect(courtPickable(COURT)).toBe(true);
    expect(courtPickable({ ...COURT, fitsFree: 0 })).toBe(false);
  });

  it('is the pick when its club and hour are the pick’s', () => {
    expect(isPickedCourt(COURT, PICK)).toBe(true);
    expect(isPickedCourt({ ...COURT, startsAt: '2026-10-03T17:00:00Z' }, PICK)).toBe(false);
    expect(isPickedCourt({ ...COURT, club: { id: 'club-2' } }, PICK)).toBe(false);
    expect(isPickedCourt(COURT, undefined)).toBe(false);
  });
});

describe('a yes on a post already happening', () => {
  const post = {
    proposalId: 'p-9',
    kind: 'competitive',
    startsAt: '2026-10-03T15:00:00Z',
    club: { id: 'club-1', name: 'Bonarka Arena' },
    shareGrosze: 3200,
    bookBy: '2026-10-03T13:00:00Z',
    peopleIn: [],
    openSeats: 2,
  } as const;

  it('is a free vote while more than its seat is open — a challenge, as the post is dealt', () => {
    expect(yesOnPost(post)).toEqual({
      proposalId: 'p-9',
      type: 'CHALLENGE',
      court: 'COURT_AVAILABLE',
    });
  });

  it('books the game on its last open seat, as the card’s Book it now does', () => {
    expect(yesOnPost({ ...post, openSeats: 1 }).court).toBe('BOOK_IT_NOW');
  });
});

describe('the number in a cell', () => {
  it('is the count up to the cap, and the cap with a plus past it', () => {
    expect(fitsShown(cell({ fitsFree: 3 }))).toEqual({ count: 3, more: false });
    expect(fitsShown(cell({ fitsFree: FITS_CAP }))).toEqual({ count: FITS_CAP, more: false });
    expect(fitsShown(cell({ fitsFree: 9 }))).toEqual({ count: FITS_CAP, more: true });
  });

  it('is nothing on a dead cell', () => {
    expect(fitsShown(cell({ fitsFree: 0 }))).toBeUndefined();
  });
});

describe('the level steppers — narrow it, not widen it (Q78)', () => {
  it('start at the engine’s window, and send nothing for a bound left there', () => {
    expect(narrowedBounds(ENGINE, UNNARROWED)).toEqual(ENGINE);
    expect(levelAsk(UNNARROWED)).toEqual({});
  });

  it('move a bound inward a step of 0,05, and send it', () => {
    const lower = stepBound(ENGINE, UNNARROWED, 'low', 'up');
    expect(lower).toEqual({ kind: 'moved', narrowing: { low: 261 } });
    if (lower.kind !== 'moved') throw new Error('moved');
    expect(narrowedBounds(ENGINE, lower.narrowing)).toEqual({ low: 2.61, high: 2.86 });
    expect(levelAsk(lower.narrowing)).toEqual({ levelLow: 2.61 });

    const upper = stepBound(ENGINE, UNNARROWED, 'high', 'down');
    expect(upper).toEqual({ kind: 'moved', narrowing: { high: 281 } });
    if (upper.kind !== 'moved') throw new Error('moved');
    expect(levelAsk(upper.narrowing)).toEqual({ levelHigh: 2.81 });
  });

  it('never drift off the hundredth however many steps are taken', () => {
    let narrowing = UNNARROWED;
    for (let press = 0; press < 7; press += 1) {
      const step = stepBound({ low: 2.07, high: 3.33 }, narrowing, 'low', 'up');
      if (step.kind !== 'moved') throw new Error('moved');
      narrowing = step.narrowing;
    }
    expect(narrowedBounds({ low: 2.07, high: 3.33 }, narrowing).low).toBe(2.42);
    expect(levelAsk(narrowing)).toEqual({ levelLow: 2.42 });
  });

  it('bounce a bound pushed past the engine’s own', () => {
    expect(stepBound(ENGINE, UNNARROWED, 'low', 'down')).toEqual({ kind: 'bounced' });
    expect(stepBound(ENGINE, UNNARROWED, 'high', 'up')).toEqual({ kind: 'bounced' });
  });

  it('let a narrowed bound back out as far as the engine’s — and there it sends nothing again', () => {
    expect(stepBound(ENGINE, { low: 266 }, 'low', 'down')).toEqual({
      kind: 'moved',
      narrowing: { low: 261 },
    });
    expect(stepBound(ENGINE, { low: 261, high: 281 }, 'high', 'up')).toEqual({
      kind: 'moved',
      narrowing: { low: 261 },
    });
  });

  it('come back to an engine window that moved, rather than past it', () => {
    // Narrowed to 2,61 against 2,56–2,86; the engine now reads 2,58 — one press is the engine's.
    expect(stepBound({ low: 2.58, high: 2.86 }, { low: 261 }, 'low', 'down')).toEqual({
      kind: 'moved',
      narrowing: {},
    });
  });

  it('shut a bound that would pass the other — the range never turns inside out', () => {
    // 2,56–2,86 is six steps wide: the two bounds meet at 2,71.
    const met = { low: 271, high: 271 };
    expect(narrowedBounds(ENGINE, met)).toEqual({ low: 2.71, high: 2.71 });
    expect(stepBound(ENGINE, met, 'low', 'up')).toEqual({ kind: 'shut' });
    expect(stepBound(ENGINE, met, 'high', 'down')).toEqual({ kind: 'shut' });
  });
});

describe('who a game may be for (mock 18)', () => {
  it('offers Mixed pairs only in doubles', () => {
    expect(whoOffered(true)).toEqual(['ANYONE', 'MEN', 'WOMEN', 'MIXED_PAIRS']);
    expect(whoOffered(false)).toEqual(['ANYONE', 'MEN', 'WOMEN']);
  });

  it('reads a Mixed pairs draft as Anyone in a sport played one a side', () => {
    expect(draftWho({ ...NEW_DRAFT, who: 'MIXED_PAIRS' }, false)).toBe('ANYONE');
    expect(draftWho({ ...NEW_DRAFT, who: 'MIXED_PAIRS' }, true)).toBe('MIXED_PAIRS');
    expect(draftWho({ ...NEW_DRAFT, who: 'WOMEN' }, false)).toBe('WOMEN');
  });
});

describe('the draft’s sport', () => {
  it('is the one chosen, else the page’s while the player may post in it, else the first', () => {
    expect(draftSport({ ...NEW_DRAFT, sport: 'tennis' }, ['padel', 'tennis'], 'padel')).toBe(
      'tennis',
    );
    expect(draftSport(NEW_DRAFT, ['padel', 'tennis'], 'tennis')).toBe('tennis');
    expect(draftSport(NEW_DRAFT, ['padel', 'tennis'], 'squash')).toBe('padel');
    expect(draftSport(NEW_DRAFT, [], 'squash')).toBe('squash');
  });
});

describe('the draft', () => {
  const narrowed: PostDraft = {
    ...NEW_DRAFT,
    sport: 'padel',
    kind: 'competitive',
    who: 'MIXED_PAIRS',
    narrowing: { low: 266, high: 281 },
    week: 2,
    pick: PICK,
  };

  it('starts as anybody, the engine’s window, this week and no pick', () => {
    expect(NEW_DRAFT).toEqual({ who: 'ANYONE', narrowing: UNNARROWED, week: 1 });
  });

  it('a sport resets the level range and clears the pick, keeping who where the sport has it', () => {
    expect(withSport(narrowed, 'badminton', true)).toEqual({
      ...narrowed,
      sport: 'badminton',
      narrowing: UNNARROWED,
      pick: undefined,
    });
  });

  it('a sport played one a side takes Mixed pairs back to Anyone', () => {
    expect(withSport(narrowed, 'tennis', false).who).toBe('ANYONE');
    expect(withSport({ ...narrowed, who: 'WOMEN' }, 'tennis', false).who).toBe('WOMEN');
  });

  it('a kind re-seeds the level range — the engine’s window is the kind’s — and keeps the pick', () => {
    expect(withKind(narrowed, 'forFun')).toEqual({
      ...narrowed,
      kind: 'forFun',
      narrowing: UNNARROWED,
    });
  });

  it('who keeps everything else', () => {
    expect(withWho(narrowed, 'WOMEN')).toEqual({ ...narrowed, who: 'WOMEN' });
  });

  it('a pick replaces the last, and goes when removed', () => {
    const other = { ...PICK, clubId: 'club-2', startsAt: '2026-10-03T17:00:00Z' };
    expect(withPick(narrowed, other).pick).toEqual(other);
    expect(withoutPick(narrowed).pick).toBeUndefined();
  });

  it('turning the week keeps the pick — it may be in the other week', () => {
    expect(withWeek(narrowed, 1)).toEqual({ ...narrowed, week: 1 });
  });
});
