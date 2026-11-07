import {
  courtsByDay,
  freeStepOf,
  isCourtGone,
  isShownCourt,
  refusalOf,
  sidesOn,
  type FriendsCard,
  type FriendsCourt,
} from './friendsCard';

const NOW = Date.parse('2026-11-05T18:00:00Z'); // Thursday 19:00 in Kraków

function court(startsAt: string, overrides: Partial<FriendsCourt> = {}): FriendsCourt {
  return {
    startsAt,
    club: { id: 'ogrody', name: 'Ogrody 33' },
    courtId: `court-${startsAt}`,
    courtName: 'Court 3',
    indoor: true,
    shareGrosze: 2500,
    homeClubFull: false,
    busy: [],
    ...overrides,
  };
}

describe('a row’s tint', () => {
  it('is brightest with everybody free, and one step dimmer for each one busy, to three', () => {
    expect(freeStepOf(court('2026-11-07T09:00:00Z'))).toBe(0);
    expect(freeStepOf(court('2026-11-07T09:00:00Z', { busy: ['ania'] }))).toBe(1);
    expect(freeStepOf(court('2026-11-07T09:00:00Z', { busy: ['a', 'b'] }))).toBe(2);
    expect(freeStepOf(court('2026-11-07T09:00:00Z', { busy: ['a', 'b', 'c'] }))).toBe(3);
  });

  it('stays at the dimmest when nobody is free', () => {
    expect(freeStepOf(court('2026-11-07T09:00:00Z', { busy: ['a', 'b', 'c', 'd'] }))).toBe(3);
  });
});

describe('Find a court’s days', () => {
  it('groups the rows by the day they are on, in the order served', () => {
    const rows = [
      court('2026-11-06T18:00:00Z'),
      court('2026-11-06T19:30:00Z'),
      court('2026-11-07T09:00:00Z'),
      court('2026-11-07T09:00:00Z', { courtId: 'court-1' }),
      court('2026-11-14T19:00:00Z'),
    ];

    const days = courtsByDay(rows, NOW);

    expect(days.map((day) => [day.when, day.courts.length])).toEqual([
      [{ kind: 'tomorrow' }, 2],
      [{ kind: 'weekday', weekday: 6 }, 2],
      [{ kind: 'dated', weekday: 6, day: '2026-11-14' }, 1],
    ]);
  });

  it('is nothing for no rows', () => {
    expect(courtsByDay([], NOW)).toEqual([]);
  });
});

describe('the court the card shows', () => {
  it('is the row with its court and its hour', () => {
    const shown = court('2026-11-07T09:00:00Z');

    expect(isShownCourt(shown, shown)).toBe(true);
    expect(isShownCourt(court('2026-11-07T09:00:00Z', { courtId: 'other' }), shown)).toBe(false);
    expect(isShownCourt(shown, undefined)).toBe(false);
  });
});

describe('the sides, as people', () => {
  const card: Pick<FriendsCard, 'sides'> = {
    sides: { yours: ['me', 'ewa'], theirs: ['magda', 'ania'] },
  };
  const people = [
    { playerId: 'ewa', name: 'ewa.m', level: 2.6 },
    { playerId: 'magda', name: 'magda.p', level: 2.66 },
    { playerId: 'ania', name: 'ania.k' },
  ];

  it('marks the reader first on their side, names each friend with their Level, and leaves a stranger unnamed', () => {
    expect(sidesOn(card, people, 2.71)).toEqual({
      yours: [
        { playerId: 'me', isYou: true, isIn: false, level: 2.71 },
        { playerId: 'ewa', isYou: false, isIn: false, name: 'ewa.m', level: 2.6 },
      ],
      theirs: [
        { playerId: 'magda', isYou: false, isIn: false, name: 'magda.p', level: 2.66 },
        { playerId: 'ania', isYou: false, isIn: false, name: 'ania.k' },
      ],
    });
  });
});

describe('what a refused read was', () => {
  it('is one of the line-up’s three refusals, or nothing', () => {
    expect(refusalOf('cannot_play_together')).toBe('cannot_play_together');
    expect(refusalOf('not_a_friend')).toBe('not_a_friend');
    expect(refusalOf('block_state_unavailable')).toBeUndefined();
    expect(refusalOf(undefined)).toBeUndefined();
  });

  it('is a court gone when the court picked is no longer for sale', () => {
    expect(isCourtGone('court_hour_not_for_sale')).toBe(true);
    expect(isCourtGone('no_level')).toBe(false);
  });
});
