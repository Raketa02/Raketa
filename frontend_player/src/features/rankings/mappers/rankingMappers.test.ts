/**
 * **The ranking's wire boundary** ([#775](https://github.com/Rakieta02/Rakieta/issues/775)) — every
 * card state, the chip, the gap line and a row, and the absences: a field the server sends `null`
 * is left out rather than turned into a nought, and what this build cannot read is drawn as nothing
 * rather than guessed.
 */

import type { components } from '@/generated/schema';

import { toGeneralPage, toRanking, toTopTen } from './rankingMappers';

type Wire = components['schemas'];

function card(over: Partial<Wire['PlaceCardSchema']> = {}): Wire['PlaceCardSchema'] {
  return {
    state: 'LISTED',
    results: 14,
    results_to_enter: 5,
    place: 7,
    of: 13,
    level: 2.71,
    chip: { kind: 'UP', places: 1 },
    gap_line: {
      above: { nickname: 'Karol', gap: 0.04, wins: 1, tied: false },
      below: { nickname: 'Zofia', gap: 0.02 },
      top_of_the_list: false,
    },
    ...over,
  };
}

function row(over: Partial<Wire['RankedRowSchema']> = {}): Wire['RankedRowSchema'] {
  return {
    place: 1,
    player_id: 'p-ines',
    nickname: 'Inés',
    photo_id: 'f-1',
    photo_url: 'https://photos.example/ines.jpg',
    form: ['WIN', 'WIN', 'LOSS'],
    chip: { kind: 'DOWN', places: 1 },
    level: 3.4,
    is_you: false,
    ...over,
  };
}

function response(over: Partial<Wire['RankingResponse']> = {}): Wire['RankingResponse'] {
  return {
    sport: 'PADEL',
    view: 'GENERAL',
    card: card(),
    listed: 13,
    podium: [],
    rows: [],
    next: null,
    ...over,
  };
}

describe('the place card', () => {
  it('reads a listed card whole: place, of, level, chip and both parts of the gap line', () => {
    expect(toRanking(response()).card).toEqual({
      state: 'LISTED',
      place: 7,
      of: 13,
      level: 2.71,
      chip: { kind: 'UP', places: 1 },
      gapLine: {
        kind: 'between',
        above: { nickname: 'Karol', gap: 0.04, wins: 1, tied: false },
        below: { nickname: 'Zofia', gap: 0.02 },
      },
    });
  });

  it('leaves the win count out where the server sends none, and either part where there is nobody', () => {
    const served = card({
      gap_line: {
        above: { nickname: 'Karol', gap: 0.31, wins: null, tied: false },
        below: null,
        top_of_the_list: false,
      },
    });

    expect(toRanking(response({ card: served })).card).toMatchObject({
      gapLine: { kind: 'between', above: { nickname: 'Karol', gap: 0.31, tied: false } },
    });
    const line = (toRanking(response({ card: served })).card as { gapLine: object }).gapLine;
    expect('below' in line).toBe(false);
    expect('wins' in (line as { above: object }).above).toBe(false);
  });

  it('reads first place as the whole line, Top of the list', () => {
    const served = card({
      place: 1,
      gap_line: { above: null, below: null, top_of_the_list: true },
    });

    expect(toRanking(response({ card: served })).card).toMatchObject({
      state: 'LISTED',
      gapLine: { kind: 'top' },
    });
  });

  it('reads the not-listed cards with only what they say', () => {
    const notListed = { place: null, of: null, level: null, chip: null, gap_line: null };

    expect(
      toRanking(response({ card: card({ ...notListed, state: 'NEEDS_RESULTS', results: 2 }) }))
        .card,
    ).toEqual({ state: 'NEEDS_RESULTS', results: 2, resultsToEnter: 5 });
    expect(
      toRanking(response({ card: card({ ...notListed, state: 'NO_LEVEL', results: 0 }) })).card,
    ).toEqual({ state: 'NO_LEVEL', resultsToEnter: 5 });
    for (const state of ['OFF_THE_LIST', 'JUST_YOU', 'NO_FRIEND_LISTED'] as const) {
      expect(toRanking(response({ card: card({ ...notListed, state }) })).card).toEqual({ state });
    }
  });

  it('draws no card where a placed one comes without its place, rather than a guess', () => {
    expect(toRanking(response({ card: card({ place: null }) })).card).toBeUndefined();
    expect(toRanking(response({ card: card({ level: null }) })).card).toBeUndefined();
  });

  it('draws no card in a state this build has never heard of — HIDDEN, retired with its switch, among them', () => {
    expect(
      toRanking(response({ card: card({ state: 'HIDDEN' as Wire['CardState'] }) })).card,
    ).toBeUndefined();
    expect(
      toRanking(response({ card: card({ state: 'RETIRED' as Wire['CardState'] }) })).card,
    ).toBeUndefined();
  });
});

describe('the chip', () => {
  it('reads each kind, a count only with up and down', () => {
    const chipOf = (chip: Wire['ChipSchema']) =>
      toRanking(response({ rows: [row({ chip })] })).rows[0]?.chip;

    expect(chipOf({ kind: 'UP', places: 2 })).toEqual({ kind: 'UP', places: 2 });
    expect(chipOf({ kind: 'DOWN', places: 1 })).toEqual({ kind: 'DOWN', places: 1 });
    expect(chipOf({ kind: 'SAME', places: null })).toEqual({ kind: 'SAME' });
    expect(chipOf({ kind: 'NEW', places: null })).toEqual({ kind: 'NEW' });
  });

  it('is left out of a row where up or down comes with no count', () => {
    const [read] = toRanking(
      response({ rows: [row({ chip: { kind: 'UP', places: null } })] }),
    ).rows;

    expect(read).toBeDefined();
    expect('chip' in read!).toBe(false);
  });
});

describe('a row', () => {
  it('reads the place, the face, the form oldest first, the level and whose it is', () => {
    expect(toRanking(response({ rows: [row()] })).rows).toEqual([
      {
        place: 1,
        playerId: 'p-ines',
        nickname: 'Inés',
        photoUrl: 'https://photos.example/ines.jpg',
        form: ['WIN', 'WIN', 'LOSS'],
        chip: { kind: 'DOWN', places: 1 },
        level: 3.4,
        isYou: false,
      },
    ]);
  });

  it('leaves the photo out when there is none, so the face draws the poster', () => {
    const [read] = toRanking(
      response({ rows: [row({ photo_id: null, photo_url: null, is_you: true })] }),
    ).rows;

    expect('photoUrl' in read!).toBe(false);
    expect(read!.isYou).toBe(true);
  });
});

describe('the page', () => {
  it('carries the view, the count listed and the podium as served', () => {
    const steps = [
      row(),
      row({ place: 2, player_id: 'p-stas' }),
      row({ place: 3, player_id: 'p-piotr' }),
    ];
    const ranking = toRanking(response({ podium: steps, rows: steps }));

    expect(ranking.view).toBe('GENERAL');
    expect(ranking.listed).toBe(13);
    expect(ranking.podium.map((one) => one.place)).toEqual([1, 2, 3]);
    expect(ranking.rows).toHaveLength(3);
  });
});

describe('the cursors (#776)', () => {
  it('carries the main read’s cursor below its first page, and none when that page is the whole list', () => {
    expect(toRanking(response({ next: 'k-50' })).next).toBe('k-50');
    expect('next' in toRanking(response({ next: null }))).toBe(false);
  });

  it('reads a page of General: its rows, and the cursors either side, each only where there is one', () => {
    const page = toGeneralPage({
      sport: 'PADEL',
      listed: 480,
      rows: [row({ place: 51, player_id: 'p-51' })],
      previous: 'k-51',
      next: 'k-100',
    });

    expect(page.rows.map((one) => one.playerId)).toEqual(['p-51']);
    expect(page.previous).toBe('k-51');
    expect(page.next).toBe('k-100');

    const ends = toGeneralPage({ sport: 'PADEL', listed: 3, rows: [], previous: null, next: null });
    expect('previous' in ends).toBe(false);
    expect('next' in ends).toBe(false);
  });
});

describe('Top 10 (#805)', () => {
  function card(over: Partial<Wire['TopTenPlayerSchema']> = {}): Wire['TopTenPlayerSchema'] {
    return {
      place: 1,
      player_id: 'p-ines',
      nickname: 'ines.d',
      photo_id: 'f-1',
      photo_url: 'https://photos.example/ines.jpg',
      level: 3.4,
      chip: { kind: 'DOWN', places: 1 },
      is_you: false,
      ...over,
    };
  }

  it('reads the sport, whether anybody is ranked anywhere, and every card in order', () => {
    const topTen = toTopTen({
      sport: 'SQUASH',
      anyone_listed: true,
      players: [
        card(),
        card({ place: 2, player_id: 'p-me', chip: { kind: 'UP', places: 2 }, is_you: true }),
      ],
    });

    expect(topTen).toEqual({
      sport: 'squash',
      anyoneListed: true,
      players: [
        {
          place: 1,
          playerId: 'p-ines',
          nickname: 'ines.d',
          photoUrl: 'https://photos.example/ines.jpg',
          level: 3.4,
          chip: { kind: 'DOWN', places: 1 },
          isYou: false,
        },
        {
          place: 2,
          playerId: 'p-me',
          nickname: 'ines.d',
          photoUrl: 'https://photos.example/ines.jpg',
          level: 3.4,
          chip: { kind: 'UP', places: 2 },
          isYou: true,
        },
      ],
    });
  });

  it('leaves out a photograph and a chip the server sends none of — the poster, and no chip', () => {
    const [player] = toTopTen({
      sport: 'PADEL',
      anyone_listed: true,
      players: [card({ photo_id: null, photo_url: null, chip: null })],
    })!.players;

    expect('photoUrl' in player!).toBe(false);
    expect('chip' in player!).toBe(false);
  });

  it('draws no chip for a move this build cannot read', () => {
    const [player] = toTopTen({
      sport: 'PADEL',
      anyone_listed: true,
      players: [card({ chip: { kind: 'SIDEWAYS' as 'UP', places: 1 } })],
    })!.players;

    expect('chip' in player!).toBe(false);
  });

  it('reads nothing at all from a sport this build has never heard of', () => {
    expect(
      toTopTen({ sport: 'PICKLEBALL' as 'PADEL', anyone_listed: true, players: [card()] }),
    ).toBeUndefined();
  });
});
