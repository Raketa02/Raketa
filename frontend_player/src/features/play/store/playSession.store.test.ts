import type { WeekCell } from '@/shared/vocabulary/week';

import { differsFromProfile } from '../domain/workingWeek';

import { endPlaySession, usePlaySession } from './playSession.store';

const TUESDAY_EVENING: WeekCell = { day: 2, part: 'evening' };
const SATURDAY_MORNING: WeekCell = { day: 6, part: 'morning' };
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
    read().toggleWeekCell({ day: 1, part: 'morning' });

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
  it('takes the week and the line-up with it', () => {
    read().enter(PROFILE_WEEK);
    read().seat('search-1', 'player-a');

    endPlaySession();

    expect(read().week).toBeUndefined();
    expect(read().lineup).toBeUndefined();
  });

  it('re-entering seeds a fresh week and no line-up, whatever the last visit built', () => {
    read().enter(PROFILE_WEEK);
    read().toggleWeekCell({ day: 1, part: 'morning' });
    read().seat('search-1', 'player-a');

    endPlaySession();
    read().enter(PROFILE_WEEK);

    expect(read().week).toEqual(PROFILE_WEEK);
    expect(read().lineup).toBeUndefined();
  });
});
