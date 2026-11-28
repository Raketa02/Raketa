/**
 * **Reading a page of General** ([#776](https://github.com/Rakieta02/Rakieta/issues/776)) — which route
 * each page is read from, and what comes back: the list's own first page is the main read, with the
 * card and the podium; every other page is the rows route, its cursor handed back as it came. Driven
 * through the real HTTP layer with only the socket faked.
 */

import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { readGeneralPage } from './readGeneralPage';

const ROWS_PATH = '/api/v1/rankings/PADEL/general/rows';
const MAIN_PATH = '/api/v1/rankings/PADEL';

function row(place: number): Wire['RankedRowSchema'] {
  return {
    place,
    player_id: `p-${place}`,
    nickname: `player.${place}`,
    photo_id: null,
    photo_url: null,
    form: [],
    chip: { kind: 'SAME', places: null },
    level: 3 - place / 100,
    is_you: false,
  };
}

const PAGE: Wire['GeneralPageResponse'] = {
  sport: 'PADEL',
  listed: 480,
  rows: [row(51)],
  previous: 'k-51',
  next: 'k-100',
};

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  transport.on('GET', ROWS_PATH, () => json(PAGE));
});

afterEach(() => transport.restore());

const asked = () => transport.requestsTo('GET', ROWS_PATH).map((one) => one.path.split('?')[1]);

describe('readGeneralPage', () => {
  it('reads the list’s first page as the main read, carrying the card and the cursor below', async () => {
    transport.on('GET', MAIN_PATH, () =>
      json<Wire['RankingResponse']>({
        sport: 'PADEL',
        view: 'GENERAL',
        card: {
          state: 'OFF_THE_LIST',
          results: 9,
          results_to_enter: 5,
          place: null,
          of: null,
          level: null,
          chip: null,
          gap_line: null,
        },
        listed: 480,
        podium: [],
        rows: [row(1)],
        next: 'k-50',
      }),
    );

    const read = await readGeneralPage('padel', { at: 'top' });

    expect(transport.requestsTo('GET', MAIN_PATH)[0]?.path).toBe(`${MAIN_PATH}?view=GENERAL`);
    expect(read.rows.map((one) => one.place)).toEqual([1]);
    expect(read.next).toBe('k-50');
    expect('previous' in read).toBe(false);
    expect(read.ranking?.card).toEqual({ state: 'OFF_THE_LIST' });
    expect(asked()).toEqual([]);
  });

  it('reads every other page from the rows route, the cursor handed back as it came', async () => {
    await readGeneralPage('padel', { at: 'aroundMe' });
    await readGeneralPage('padel', { at: 'after', cursor: 'k=50/a' });
    const above = await readGeneralPage('padel', { at: 'before', cursor: 'k-51' });

    expect(asked()).toEqual(['around_me=true', 'after=k%3D50%2Fa', 'before=k-51']);
    expect(above).toEqual({
      rows: [expect.objectContaining({ place: 51, playerId: 'p-51' })],
      previous: 'k-51',
      next: 'k-100',
    });
    expect('ranking' in above).toBe(false);
  });
});
