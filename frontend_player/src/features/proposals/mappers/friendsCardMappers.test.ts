import type { components } from '@/generated/schema';

import { toFriendsCard, toFriendsCardQuery, toFriendsCourts } from './friendsCardMappers';

type Wire = components['schemas'];

const ROW: Wire['FriendsCourtSchema'] = {
  starts_at: '2026-11-07T09:00:00Z',
  club: { id: 'wisla', name: 'Wisła Park' },
  court_id: 'court-3',
  court_name: 'Court 3',
  indoor: false,
  share_grosze: 2500,
  home_club_full: true,
  free_count: 3,
  busy: ['ania'],
};

const OVERLAP: Wire['DeckOverlapSchema'] = {
  grade: 'SLIM',
  cells: [{ day: 6, range: 'MORNING', shade: 'BRIGHT' }],
  game: { day: 6, range: 'MORNING' },
};

function card(overrides: Partial<Wire['FriendsCardResponse']> = {}): Wire['FriendsCardResponse'] {
  return {
    pool_id: 'g-1',
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    home_club: { id: 'ogrody', name: 'Ogrody 33' },
    sides: { yours: ['me', 'ewa'], theirs: ['magda', 'ania'] },
    forecast: { pct: 87, provisional: false },
    vibe: null,
    court: ROW,
    overlap: OVERLAP,
    cut_off: '2026-11-06T09:00:00Z',
    ...overrides,
  };
}

describe('toFriendsCard', () => {
  it('reads the sides, the forecast, the court with its marker, the overlap and the cut-off', () => {
    expect(toFriendsCard(card())).toEqual({
      kind: 'competitive',
      homeClub: { id: 'ogrody', name: 'Ogrody 33' },
      sides: { yours: ['me', 'ewa'], theirs: ['magda', 'ania'] },
      forecast: { pct: 87, provisional: false },
      court: {
        startsAt: '2026-11-07T09:00:00Z',
        club: { id: 'wisla', name: 'Wisła Park' },
        courtId: 'court-3',
        courtName: 'Court 3',
        indoor: false,
        shareGrosze: 2500,
        homeClubFull: true,
        busy: ['ania'],
      },
      overlap: {
        grade: 'SLIM',
        cells: [{ day: 6, range: 'MORNING', shade: 'BRIGHT' }],
        game: { day: 6, range: 'MORNING' },
      },
      cutOff: '2026-11-06T09:00:00Z',
    });
  });

  it('leaves off what the read could not give: no forecast, no court, no overlap', () => {
    expect(
      toFriendsCard(card({ forecast: null, court: null, overlap: null, cut_off: null })),
    ).toEqual({
      kind: 'competitive',
      homeClub: { id: 'ogrody', name: 'Ogrody 33' },
      sides: { yours: ['me', 'ewa'], theirs: ['magda', 'ania'] },
    });
  });

  // #842 (ADR-0207 §5): a For-fun card says its Social vibe, and the server sends no forecast.
  it('reads a For-fun card’s kind and its Social vibe, with no forecast', () => {
    const read = toFriendsCard(card({ kind: 'FOR_FUN', forecast: null, vibe: { pct: 67 } }));

    expect(read.kind).toBe('forFun');
    expect(read.vibe).toEqual({ pct: 67 });
    expect(read).not.toHaveProperty('forecast');
  });

  it('reads no vibe where nobody seated holds a tag, or from an older server that sends none', () => {
    expect(toFriendsCard(card({ kind: 'FOR_FUN', forecast: null }))).not.toHaveProperty('vibe');
    const older = card({ kind: 'FOR_FUN', forecast: null }) as Partial<Wire['FriendsCardResponse']>;
    delete older.vibe;
    expect(toFriendsCard(older as Wire['FriendsCardResponse'])).not.toHaveProperty('vibe');
  });
});

describe('toFriendsCourts', () => {
  it('reads every row, in the order served, and a club with no name', () => {
    const read = toFriendsCourts({
      pool_id: 'g-1',
      sport: 'PADEL',
      home_club: { id: 'ogrody', name: null },
      courts: [ROW, { ...ROW, court_id: 'court-1', home_club_full: false, busy: [] }],
    });

    expect(read.homeClub).toEqual({ id: 'ogrody' });
    expect(read.courts.map((row) => [row.courtId, row.homeClubFull, row.busy])).toEqual([
      ['court-3', true, ['ania']],
      ['court-1', false, []],
    ]);
  });
});

describe('toFriendsCardQuery', () => {
  it('spells the sport, the kind and every friend, and the sides and the court once chosen', () => {
    expect(
      toFriendsCardQuery('padel', {
        kind: 'forFun',
        friendIds: ['ewa', 'magda', 'ania'],
        partnerId: 'magda',
        court: { courtId: 'court-3', startsAt: '2026-11-07T09:00:00Z' },
      }),
    ).toBe(
      'sport=PADEL&friend_ids=ewa&friend_ids=magda&friend_ids=ania&kind=FOR_FUN' +
        '&partner_id=magda&court_id=court-3&starts_at=2026-11-07T09%3A00%3A00Z',
    );
  });

  it('asks for the evenest sides and the proposed court by leaving both off', () => {
    expect(toFriendsCardQuery('tennis', { kind: 'competitive', friendIds: ['ewa'] })).toBe(
      'sport=TENNIS&friend_ids=ewa&kind=COMPETITIVE',
    );
  });
});
