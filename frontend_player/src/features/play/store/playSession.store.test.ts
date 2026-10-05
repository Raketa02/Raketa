import type { WeeklyHour } from '@/shared/vocabulary/week';

import { differsFromProfile } from '../domain/workingWeek';

import { endPlaySession, usePlaySession } from './playSession.store';

const TUESDAY_EVENING: WeeklyHour = { day: 2, hour: 19 };
const SATURDAY_MORNING: WeeklyHour = { day: 6, hour: 9 };
const PROFILE_WEEK = [TUESDAY_EVENING, SATURDAY_MORNING];

const read = () => usePlaySession.getState();

beforeEach(() => {
  read().end();
});

describe('the working copy', () => {
  it('holds nothing outside a session — a cleared week is legal, so an empty one is not absence', () => {
    expect(read().week).toBeUndefined();
  });

  it('arrives already filled in from the profile, on entry', () => {
    read().enter(PROFILE_WEEK);

    expect(read().week).toEqual(PROFILE_WEEK);
  });

  it('is a copy: editing it does not reach the profile week it was seeded from', () => {
    const profile = [...PROFILE_WEEK];
    read().enter(profile);
    read().toggleWeekCell({ day: 1, hour: 9 });

    expect(profile).toEqual(PROFILE_WEEK);
    expect(differsFromProfile(read().week ?? [], profile)).toBe(true);
  });

  it('ticks and unticks a cell, and the marker follows the comparison', () => {
    read().enter(PROFILE_WEEK);
    read().toggleWeekCell(TUESDAY_EVENING);
    expect(differsFromProfile(read().week ?? [], PROFILE_WEEK)).toBe(true);

    read().toggleWeekCell(TUESDAY_EVENING);
    expect(differsFromProfile(read().week ?? [], PROFILE_WEEK)).toBe(false);
  });

  it('drops a tap made outside a session rather than beginning one', () => {
    read().toggleWeekCell(TUESDAY_EVENING);

    expect(read().week).toBeUndefined();
  });

  it('paints a dragged run onto the copy, and clears one the same way', () => {
    const run: readonly WeeklyHour[] = [
      { day: 3, hour: 18 },
      { day: 3, hour: 19 },
    ];
    read().enter(PROFILE_WEEK);

    read().paintWeekCells(run, true);
    expect(read().week).toEqual([...PROFILE_WEEK, ...run]);

    read().paintWeekCells(run, false);
    expect(read().week).toEqual(PROFILE_WEEK);
    expect(differsFromProfile(read().week ?? [], PROFILE_WEEK)).toBe(false);
  });

  it('drops a run painted outside a session rather than beginning one', () => {
    read().paintWeekCells([TUESDAY_EVENING], true);

    expect(read().week).toBeUndefined();
  });
});

describe('the cell a times rung added', () => {
  const THURSDAY_EVENING: WeeklyHour = { day: 4, hour: 19 };

  it('is nothing until a rung is taken', () => {
    read().enter(PROFILE_WEEK);

    expect(read().addedForThisSearch).toBeUndefined();
  });

  /**
   * The whole of why it is a field of its own. `week` is what travels as
   * `availability_override`, so an offered cell written into it would carry a this-search-only
   * widening into every later ask — the conflation ADR-0099 exists to prevent, arriving from
   * the client instead of the engine.
   */
  it('is not the week: the ask the next search sends is untouched', () => {
    read().enter(PROFILE_WEEK);

    read().addForThisSearch(THURSDAY_EVENING);

    expect(read().week).toEqual(PROFILE_WEEK);
    expect(differsFromProfile(read().week ?? [], PROFILE_WEEK)).toBe(false);
  });

  it('goes when the player ticks that cell for themselves — it is their own ask now', () => {
    read().enter(PROFILE_WEEK);
    read().addForThisSearch(THURSDAY_EVENING);

    read().toggleWeekCell(THURSDAY_EVENING);

    expect(read().week).toEqual([...PROFILE_WEEK, THURSDAY_EVENING]);
    expect(read().addedForThisSearch).toBeUndefined();
  });

  it('goes when a painted run crosses that cell — ticked or cleared, the player has answered it', () => {
    read().enter(PROFILE_WEEK);
    read().addForThisSearch(THURSDAY_EVENING);

    read().paintWeekCells([{ day: 4, hour: 18 }, THURSDAY_EVENING], true);

    expect(read().week).toEqual([...PROFILE_WEEK, { day: 4, hour: 18 }, THURSDAY_EVENING]);
    expect(read().addedForThisSearch).toBeUndefined();
  });

  it('stays while a run elsewhere is painted', () => {
    read().enter(PROFILE_WEEK);
    read().addForThisSearch(THURSDAY_EVENING);

    read().paintWeekCells([{ day: 1, hour: 7 }], true);

    expect(read().addedForThisSearch).toEqual(THURSDAY_EVENING);
  });

  it('stays while another cell is edited, because that edit is not about it', () => {
    read().enter(PROFILE_WEEK);
    read().addForThisSearch(THURSDAY_EVENING);

    read().toggleWeekCell(TUESDAY_EVENING);

    expect(read().addedForThisSearch).toEqual(THURSDAY_EVENING);
  });

  /** A new search cites no offer, so the mark would be a fact about a list nobody holds. */
  it('is forgotten on demand, for the search that does not carry it', () => {
    read().enter(PROFILE_WEEK);
    read().addForThisSearch(THURSDAY_EVENING);

    read().clearAddedForThisSearch();

    expect(read().addedForThisSearch).toBeUndefined();
  });

  it('drops a rung taken outside a session rather than beginning one', () => {
    read().addForThisSearch(THURSDAY_EVENING);

    expect(read().addedForThisSearch).toBeUndefined();
  });
});

describe('the line-up', () => {
  it('is absent until somebody is added', () => {
    read().enter(PROFILE_WEEK);

    expect(read().lineup).toBeUndefined();
  });

  it('records the search each person came off, and keeps them in seat order', () => {
    read().seat('search-1', 'player-a');
    read().seat('search-1', 'player-b');

    expect(read().lineup).toEqual({
      originSearchId: 'search-1',
      seats: ['player-a', 'player-b'],
    });
  });

  it('holds ids and nothing else — the names and levels are read back off the search', () => {
    read().seat('search-1', 'player-a');

    expect(read().lineup?.seats).toEqual(['player-a']);
  });

  it('adds nobody twice', () => {
    read().seat('search-1', 'player-a');
    read().seat('search-1', 'player-a');

    expect(read().lineup?.seats).toEqual(['player-a']);
  });

  it('starts again rather than mixing two searches — the forecast would refuse the mixture', () => {
    read().seat('search-1', 'player-a');
    read().seat('search-2', 'player-b');

    expect(read().lineup).toEqual({ originSearchId: 'search-2', seats: ['player-b'] });
  });

  it('takes somebody off, and the last one out leaves no empty line-up behind', () => {
    read().seat('search-1', 'player-a');
    read().seat('search-1', 'player-b');

    read().unseat('player-a');
    expect(read().lineup).toEqual({ originSearchId: 'search-1', seats: ['player-b'] });

    read().unseat('player-b');
    expect(read().lineup).toBeUndefined();
  });

  it('is discarded on its own, keeping the week the player is searching on', () => {
    read().enter(PROFILE_WEEK);
    read().seat('search-1', 'player-a');

    read().discardLineup();

    expect(read().lineup).toBeUndefined();
    expect(read().week).toEqual(PROFILE_WEEK);
  });
});

describe('when a Play session ends', () => {
  it('takes the week, the line-up and the added cell with it', () => {
    read().enter(PROFILE_WEEK);
    read().seat('search-1', 'player-a');
    read().addForThisSearch({ day: 4, hour: 19 });

    endPlaySession();

    expect(read().week).toBeUndefined();
    expect(read().lineup).toBeUndefined();
    expect(read().addedForThisSearch).toBeUndefined();
  });

  it('re-entering seeds a fresh week and no line-up, whatever the last visit built', () => {
    read().enter(PROFILE_WEEK);
    read().toggleWeekCell({ day: 1, hour: 9 });
    read().seat('search-1', 'player-a');
    read().addForThisSearch({ day: 4, hour: 19 });

    endPlaySession();
    read().enter(PROFILE_WEEK);

    expect(read().week).toEqual(PROFILE_WEEK);
    expect(read().lineup).toBeUndefined();
    expect(read().addedForThisSearch).toBeUndefined();
  });
});
