import type { Wire } from '@/test-support/transport';

import { KUBA, ZOFIA, seatToFill } from '@/test-support/groupDeck';
import {
  FEW,
  HOT,
  forFunFit,
  freeCourt,
  postStillFilling,
  postingGrid,
  postingSlot,
} from '@/test-support/posting';

import { toPosted, toPostingGrid, toPostingSlot, toWireAsk } from './postingMappers';

describe('the posting grid', () => {
  it('reads the week, the clock, both level ranges, the open seats and every cell', () => {
    const read = toPostingGrid(
      postingGrid({
        cells: {
          '2026-10-03:EVENING': { ...HOT, happening: true },
          '2026-10-01:MORNING': { ...FEW, outside_your_hours: true },
          '2026-09-30:MORNING': { past: true },
        },
        level_range: { low: 2.61, high: 2.86 },
      }),
    );

    expect(read.week).toBe(1);
    expect(read.readAt).toBe('2026-09-30T08:00:00.000Z');
    expect(read.levelRange).toEqual({ low: 2.61, high: 2.86 });
    expect(read.engineLevelRange).toEqual({ low: 2.56, high: 2.86 });
    expect(read.openSeats).toBe(3);
    expect(read.days.map((day) => day.day)).toEqual([
      '2026-09-30',
      '2026-10-01',
      '2026-10-02',
      '2026-10-03',
      '2026-10-04',
      '2026-10-05',
      '2026-10-06',
    ]);
    expect(read.days.map((day) => day.isToday)).toEqual([
      true,
      false,
      false,
      false,
      false,
      false,
      false,
    ]);
    expect(read.days[3]?.cells[2]).toEqual({
      day: '2026-10-03',
      range: 'EVENING',
      fitsFree: 5,
      bestStartsAt: '2026-10-03T17:00:00Z',
      courtFree: true,
      fullGame: true,
      outsideYourHours: false,
      past: false,
      happening: true,
    });
    expect(read.days[1]?.cells[0]).toMatchObject({ fitsFree: 2, outsideYourHours: true });
    expect(read.days[0]?.cells[0]).toMatchObject({ past: true });
  });

  it('leaves out a best hour the read has not got, and keeps the second week as two', () => {
    const wire = postingGrid({ week: 2 });
    const first = wire.days[0];
    if (first === undefined) throw new Error('a day');
    const read = toPostingGrid({
      ...wire,
      days: [{ ...first, cells: first.cells.map((cell) => ({ ...cell, best_starts_at: null })) }],
    });

    expect(read.week).toBe(2);
    expect(read.days[0]?.cells[0]).not.toHaveProperty('bestStartsAt');
  });
});

describe('a cell’s sheet', () => {
  it('reads the cell, the fits with their Level and forecast, the courts, the rescues and the posts', () => {
    const rescue = seatToFill();
    const post = postStillFilling();
    const read = toPostingSlot(
      postingSlot({
        free_courts: [freeCourt(), freeCourt({ home_club: false, distance_km: null })],
        rescues: [rescue],
        posts: [post],
      }),
    );

    expect(read).toMatchObject({ day: '2026-10-03', range: 'EVENING', openSeats: 3 });
    expect(read.cell).toMatchObject({ fitsFree: 5, courtFree: true, fullGame: true });
    expect(read.fits[0]).toEqual({
      playerId: 'd0000000-0000-4000-8000-000000000001',
      name: 'karol.t',
      level: 2.75,
      forecast: { pct: 93 },
    });
    expect(read.freeCourts[0]).toEqual({
      club: { id: 'b0000000-0000-4000-8000-000000000002', name: 'Ogrody 33' },
      homeClub: true,
      distanceKm: 2.4,
      startsAt: '2026-10-03T15:00:00Z',
      shareGrosze: 2700,
      bookBy: '2026-10-03T13:00:00Z',
      courts: 2,
      fitsFree: 4,
    });
    expect(read.freeCourts[1]).not.toHaveProperty('distanceKm');
    expect(read.rescues.map((row) => row.bookingId)).toEqual([rescue.booking_id]);
    expect(read.posts[0]).toMatchObject({
      proposalId: post.proposal_id,
      kind: 'competitive',
      club: { name: 'Bonarka Arena' },
      shareGrosze: 3200,
      challenger: { playerId: KUBA().player_id, name: 'kuba.w' },
      openSeats: 2,
    });
    expect(read.posts[0]?.peopleIn.map((person) => [person.name, person.isIn])).toEqual([
      ['kuba.w', true],
      ['ania.k', true],
    ]);
  });

  it('leaves the forecast off a fit it could not be read for, and the poster off a withdrawn post', () => {
    const wire = postingSlot();
    const read = toPostingSlot({
      ...wire,
      fits: wire.fits.map((fit) => ({ ...fit, forecast: null, level: null, nickname: null })),
      posts: [postStillFilling({ challenger: null })],
    });

    expect(read.fits[0]).toEqual({ playerId: 'd0000000-0000-4000-8000-000000000001' });
    expect(read.posts[0]).not.toHaveProperty('challenger');
  });

  // #842 (ADR-0207 §5): on a For-fun post a fit carries the Social vibe of the poster and them.
  it('reads a For-fun fit’s Social vibe, in the order served, and no forecast', () => {
    const read = toPostingSlot(
      postingSlot({ fits: [forFunFit(ZOFIA(), 83), forFunFit(KUBA(), 36)] }),
    );

    expect(read.fits.map((fit) => [fit.name, fit.vibe, fit.forecast])).toEqual([
      ['zofia.b', { pct: 83 }, undefined],
      ['kuba.w', { pct: 36 }, undefined],
    ]);
  });

  it('reads the kind the sheet was read for — what its fits’ number follows', () => {
    expect(toPostingSlot(postingSlot()).kind).toBe('competitive');
    expect(toPostingSlot(postingSlot({ kind: 'FOR_FUN' })).kind).toBe('forFun');
  });

  it('reads no vibe from an older server that sends none', () => {
    const wire = postingSlot();
    const read = toPostingSlot({
      ...wire,
      fits: wire.fits.map(({ vibe: _vibe, ...fit }) => fit as Wire['SlotFitSchema']),
    });

    expect(read.fits[0]).not.toHaveProperty('vibe');
  });

  it('drops a rescue in a sport this build cannot name', () => {
    const read = toPostingSlot(
      postingSlot({ rescues: [seatToFill({ sport: 'CURLING' as Wire['Sport'] })] }),
    );
    expect(read.rescues).toEqual([]);
  });
});

describe('the ask, onto the wire', () => {
  it('spells the sport and the kind the wire’s way and sends a bound only once it is narrowed', () => {
    expect(toWireAsk({ sport: 'padel', kind: 'forFun', who: 'MIXED_PAIRS' })).toEqual({
      sport: 'PADEL',
      kind: 'FOR_FUN',
      who: 'MIXED_PAIRS',
    });
    expect(
      toWireAsk({ sport: 'tennis', kind: 'competitive', who: 'WOMEN', levelLow: 2.61 }),
    ).toEqual({ sport: 'TENNIS', kind: 'COMPETITIVE', who: 'WOMEN', level_low: 2.61 });
  });
});

describe('the post', () => {
  it('reads the game’s id, its versions, who it was dealt to and the seats open', () => {
    expect(toPosted({ proposal_id: 'p-1', versions: 2, dealt_to: 6, open_seats: 3 })).toEqual({
      proposalId: 'p-1',
      versions: 2,
      dealtTo: 6,
      openSeats: 3,
    });
  });
});
