import type { WeekCell } from '@/shared/vocabulary/week';

import {
  differsFromProfile,
  isTicked,
  sameWeek,
  seedWorkingWeek,
  sentWeekForOrigin,
  toggleCell,
  type WorkingWeek,
} from './workingWeek';

const TUESDAY_EVENING: WeekCell = { day: 2, part: 'evening' };
const SATURDAY_MORNING: WeekCell = { day: 6, part: 'morning' };
const PROFILE: WorkingWeek = [TUESDAY_EVENING, SATURDAY_MORNING];

describe('seeding the working copy', () => {
  it('arrives already filled in from the profile', () => {
    expect(seedWorkingWeek(PROFILE)).toEqual(PROFILE);
  });

  it('is a copy, so a tap on the grid is not a tap on the profile', () => {
    const profile = [...PROFILE];
    const working = toggleCell(seedWorkingWeek(profile), { day: 1, part: 'morning' });

    expect(working).toHaveLength(3);
    expect(profile).toEqual(PROFILE);
  });
});

describe('toggling a cell', () => {
  it('ticks a cell that is not ticked, and unticks one that is', () => {
    const on = toggleCell(PROFILE, { day: 1, part: 'morning' });
    expect(isTicked(on, { day: 1, part: 'morning' })).toBe(true);

    expect(isTicked(toggleCell(on, { day: 1, part: 'morning' }), { day: 1, part: 'morning' })).toBe(
      false,
    );
  });

  it('keeps press order, so a week handed back unchanged is the same list', () => {
    expect(toggleCell(PROFILE, { day: 1, part: 'morning' })).toEqual([
      TUESDAY_EVENING,
      SATURDAY_MORNING,
      { day: 1, part: 'morning' },
    ]);
  });

  it('reads a day and a part together — the same day at another part is another cell', () => {
    expect(isTicked(PROFILE, { day: 2, part: 'morning' })).toBe(false);
  });
});

describe('whether the week differs from the profile', () => {
  it('says nothing about a week nobody has touched', () => {
    expect(differsFromProfile(seedWorkingWeek(PROFILE), PROFILE)).toBe(false);
  });

  it('reports a tick', () => {
    expect(differsFromProfile(toggleCell(PROFILE, { day: 1, part: 'morning' }), PROFILE)).toBe(
      true,
    );
  });

  it('AC-27: a slot ticked on and off again is no longer reported as changed', () => {
    // The case that decides the shape. `changed` cannot be a flag a toggle sets — this
    // player is back where they started and a flag would still be up.
    const there = toggleCell(seedWorkingWeek(PROFILE), { day: 4, part: 'afternoon' });
    const back = toggleCell(there, { day: 4, part: 'afternoon' });

    expect(differsFromProfile(there, PROFILE)).toBe(true);
    expect(differsFromProfile(back, PROFILE)).toBe(false);
  });

  it('AC-27: unticking a profile cell and ticking it again is not a change either', () => {
    const off = toggleCell(seedWorkingWeek(PROFILE), TUESDAY_EVENING);
    const on = toggleCell(off, TUESDAY_EVENING);

    expect(differsFromProfile(off, PROFILE)).toBe(true);
    expect(sameWeek(on, PROFILE)).toBe(true);
  });

  it('compares as a set, so press order is not a difference', () => {
    expect(sameWeek([SATURDAY_MORNING, TUESDAY_EVENING], PROFILE)).toBe(true);
  });

  it('compares cells, not list positions: a repeat is not a second cell', () => {
    // A scan-based comparison reports [Tue evening, Tue evening] equal to
    // [Tue evening, Sat morning] — same length, and every member of the first is in the
    // second. Nothing in this app's own toggle can produce a repeat, and a week off the wire
    // is not this app's own.
    expect(sameWeek([TUESDAY_EVENING, TUESDAY_EVENING], PROFILE)).toBe(false);
    expect(sameWeek(PROFILE, [TUESDAY_EVENING, TUESDAY_EVENING])).toBe(false);
    expect(sameWeek([TUESDAY_EVENING, TUESDAY_EVENING], [TUESDAY_EVENING])).toBe(true);
  });

  it('a cleared week is a legal week, and it is a change', () => {
    expect(sameWeek([], PROFILE)).toBe(false);
    expect(sameWeek([], [])).toBe(true);
  });
});

describe('the week a second search on one origin sends', () => {
  it('omits it where the origin ran on the profile’s own grid', () => {
    expect(sentWeekForOrigin([TUESDAY_EVENING], [TUESDAY_EVENING])).toBeUndefined();
  });

  it('sends the week the origin actually ran on where it differs', () => {
    expect(sentWeekForOrigin([TUESDAY_EVENING], [SATURDAY_MORNING])).toEqual([TUESDAY_EVENING]);
  });

  /**
   * **Unprovable is sent.** Omitting means *the grid on my profile*, not *the week the search
   * above me ran on* — so a fill or a widening with no profile read in hand would quietly run
   * on a different week from the answer it is extending, with nothing on screen to see.
   */
  it('sends it rather than omitting it when the profile cannot be read', () => {
    expect(sentWeekForOrigin([TUESDAY_EVENING], undefined)).toEqual([TUESDAY_EVENING]);
  });

  /** A cleared week is a legal ask, and it is not the same ask as *use my profile grid*. */
  it('sends an emptied week, which an omission would turn back into the profile’s', () => {
    expect(sentWeekForOrigin([], [TUESDAY_EVENING])).toEqual([]);
  });
});
