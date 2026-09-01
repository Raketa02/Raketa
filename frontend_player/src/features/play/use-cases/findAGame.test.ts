/**
 * Pressing *Search*, as one act over two requests.
 *
 * What is asserted here is the **order and the arithmetic**, both of which are invisible from
 * the screen: a search sends asks and never facts, so the radius on the slider only reaches
 * the engine by way of the profile — and if it were written *after* the search, the search
 * would have run at the old distance and the profile would have moved for no reason.
 */

import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { findAGame } from './findAGame';

const SEARCHES = '/api/v1/searches';

const TUESDAY_EVENING = { day: 2, part: 'evening' } as const;
const SATURDAY_MORNING = { day: 6, part: 'morning' } as const;

const SHORTLIST: Wire['ShortlistResponse'] = {
  search: {
    search_id: 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b',
    at: '2026-08-31T18:00:00Z',
    surface: 'SHORTLIST',
    mode: 'FOR_FUN',
    ruleset_version: 'ruleset-v1',
    engine_version: 'matchfit-v1',
    optimised_for: 'SEARCHER',
    index_stale: false,
    pool: {
      sport: 'PADEL',
      radius_km_used: 22,
      players_in_range: 7,
      window: 'THIS_WEEK',
      post_gate: true,
    },
    radius_clamp: false,
    sorts_available: ['BEST_FIT'],
    rung_offers: null,
    prompts: [{ prompt: 'KEEP_THESE_TIMES', slots: ['2:EVENING'] }],
  },
  candidates: [],
};

let transport: Transport;
const saved: number[] = [];

beforeEach(() => {
  transport = installTransport();
  saved.length = 0;
  transport.on('POST', SEARCHES, () => json(SHORTLIST));
});

afterEach(() => transport.restore());

const ASK = {
  origin: { sport: 'padel', mode: 'FOR_FUN', week: [TUESDAY_EVENING] },
  sentWeek: undefined,
  radiusKm: 22,
  profileRadiusKm: 12,
  quotes: { sportName: 'Padel', profileWeek: [TUESDAY_EVENING, SATURDAY_MORNING] },
} as const;

const saveRadius = (radiusKm: number) => {
  saved.push(radiusKm);
  return Promise.resolve();
};

describe('the radius, which the search cannot carry', () => {
  it('lands on the profile before the search runs', async () => {
    await findAGame(ASK, { saveRadius });

    expect(saved).toEqual([22]);
    // The search went out after it, which is the whole reason the two are one act: a search
    // is *asks only*, and the engine reads the radius off the profile at request time.
    expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(1);
  });

  it('is not written at all where nothing moved', async () => {
    await findAGame({ ...ASK, radiusKm: 12 }, { saveRadius });

    expect(saved).toEqual([]);
    expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(1);
  });

  // Nothing was minted, so `retryTarget` answers *the-search* and the retry is the control
  // the player already pressed — which is only true if the search never happened.
  it('leaves no search behind when it fails', async () => {
    await expect(
      findAGame(ASK, { saveRadius: () => Promise.reject(new Error('refused')) }),
    ).rejects.toThrow();

    expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(0);
  });
});

describe('what comes back', () => {
  it('folds the ask onto the id, because the envelope carries neither the sport nor the week', async () => {
    const outcome = await findAGame(ASK, { saveRadius });

    expect(outcome.record.searchId).toBe('e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b');
    expect(outcome.record.origin).toEqual(ASK.origin);
  });

  /**
   * The rows travel with the record, because the builder draws people out of them: a line-up's
   * seats are ids and nothing else, and every fact about a seated player is read back off here
   * ([#271](https://github.com/Raketa02/Raketa/issues/271)).
   */
  it('carries the rows the search ranked, which the builder seats people out of', async () => {
    const outcome = await findAGame(ASK, { saveRadius });

    expect(outcome.record.candidates.map((row) => row.playerId)).toEqual(
      SHORTLIST.candidates.flatMap((row) => ('player_id' in row ? [row.player_id] : [])),
    );
    // A shortlist seats nobody, so there is no court — absent rather than empty.
    expect(outcome.record.court).toBeUndefined();
  });

  /**
   * *"It never blocks"*, as arithmetic rather than as a rule a screen obeys.
   *
   * The prompt is on the search's own response, so a raised question is proof the search has
   * already run — there is no ordering left for a sheet to get wrong.
   */
  it('carries the questions the search raised, which therefore cannot precede it', async () => {
    const outcome = await findAGame(ASK, { saveRadius });

    expect(outcome.prompts).toEqual([
      {
        prompt: 'KEEP_THESE_TIMES',
        week: [TUESDAY_EVENING],
        profileWeek: [TUESDAY_EVENING, SATURDAY_MORNING],
      },
    ]);
    expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(1);
  });

  /**
   * The searching latch's one number, and the reason it is on the outcome at all: a count that
   * did not arrive with the answer is a count printed before there was one (#269).
   */
  it('carries the pool’s post-gate count, off the response', async () => {
    const outcome = await findAGame(ASK, { saveRadius });

    expect(outcome.playersInRange).toBe(7);
  });
});

describe('the week', () => {
  it('travels as an override only when it was improvised', async () => {
    await findAGame({ ...ASK, sentWeek: [TUESDAY_EVENING] }, { saveRadius });

    const [request] = transport.requestsTo('POST', SEARCHES);
    expect(request?.body).toEqual({
      sport: 'PADEL',
      mode: 'FOR_FUN',
      availability_override: [{ day: 2, part: 'EVENING' }],
    });
  });

  // #247: a blank grid is a legal answer, and an empty list is how the wire says it.
  it('runs a search on a cleared week', async () => {
    await findAGame({ ...ASK, sentWeek: [] }, { saveRadius });

    const [request] = transport.requestsTo('POST', SEARCHES);
    expect(request?.body).toMatchObject({ availability_override: [] });
  });
});
