import type { Wire } from '@/test-support/transport';

import { toOriginSearch, toRaisedPrompts, toRunSearchRequest } from './searchMappers';

const TUESDAY_EVENING = { day: 2, part: 'evening' } as const;

const ORIGIN = {
  sport: 'padel',
  mode: 'COMPETITIVE',
  week: [TUESDAY_EVENING],
} as const;

const QUOTED = { sportName: 'Padel', slotsOnProfile: 4 };

function shortlist(prompts?: Wire['PromptSchema'][]): Wire['ShortlistResponse'] {
  return {
    search: {
      search_id: 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b',
      at: '2026-08-31T18:00:00Z',
      surface: 'SHORTLIST',
      mode: 'COMPETITIVE',
      ruleset_version: 'ruleset-v1',
      engine_version: 'matchfit-v1',
      optimised_for: 'SEARCHER',
      index_stale: false,
      pool: {
        sport: 'PADEL',
        radius_km_used: 12,
        players_in_range: 7,
        window: 'THIS_WEEK',
        post_gate: true,
      },
      radius_clamp: false,
      sorts_available: ['BEST_FIT'],
      rung_offers: null,
      ...(prompts === undefined ? {} : { prompts }),
    },
    candidates: [],
  };
}

describe('the ask', () => {
  it('sends the sport and the mode in the wire spelling', () => {
    expect(toRunSearchRequest({ origin: ORIGIN, sentWeek: undefined })).toEqual({
      sport: 'PADEL',
      mode: 'COMPETITIVE',
    });
  });

  // "Omit it, never send `null`" — an absent override means *use the grid on my profile*.
  it('omits the override entirely when the week is the profile’s', () => {
    expect(toRunSearchRequest({ origin: ORIGIN, sentWeek: undefined })).not.toHaveProperty(
      'availability_override',
    );
  });

  it('sends the improvised week as the override', () => {
    expect(toRunSearchRequest({ origin: ORIGIN, sentWeek: [TUESDAY_EVENING] })).toMatchObject({
      availability_override: [{ day: 2, part: 'EVENING' }],
    });
  });

  // The whole of #247: a cleared week is a legal value, and an empty list is how it is said.
  it('sends a cleared week as an empty override rather than as an omission', () => {
    expect(toRunSearchRequest({ origin: ORIGIN, sentWeek: [] })).toEqual({
      sport: 'PADEL',
      mode: 'COMPETITIVE',
      availability_override: [],
    });
  });
});

describe('the record a line-up is judged against', () => {
  it('folds the ask onto the id, because the envelope carries neither', () => {
    expect(toOriginSearch(shortlist(), ORIGIN)).toEqual({
      searchId: 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b',
      origin: ORIGIN,
    });
  });
});

describe('the questions a search raises', () => {
  it('raises none where the response carries none', () => {
    expect(toRaisedPrompts(shortlist(), QUOTED)).toEqual([]);
  });

  it('counts the week the search ran on, against the count on the profile', () => {
    const raised = toRaisedPrompts(
      shortlist([{ prompt: 'KEEP_THESE_TIMES', slots: ['2:EVENING', '6:MORNING'] }]),
      QUOTED,
    );

    expect(raised).toEqual([{ prompt: 'KEEP_THESE_TIMES', slotsNow: 2, slotsWas: 4 }]);
  });

  // `()` is a cleared week and is a real offer; `None` is *not this prompt*.
  it('offers to keep a cleared week', () => {
    expect(toRaisedPrompts(shortlist([{ prompt: 'KEEP_THESE_TIMES', slots: [] }]), QUOTED)).toEqual(
      [{ prompt: 'KEEP_THESE_TIMES', slotsNow: 0, slotsWas: 4 }],
    );
  });

  it('quotes the radius and the sport off the payload and the ask', () => {
    const raised = toRaisedPrompts(
      shortlist([
        { prompt: 'KEEP_THIS_RADIUS', radius_km: 22 },
        { prompt: 'UPDATE_PLAY_INTENT', mode: 'FOR_FUN' },
        { prompt: 'REFRESH_YOUR_TIMES' },
      ]),
      QUOTED,
    );

    expect(raised).toEqual([
      { prompt: 'KEEP_THIS_RADIUS', radiusKm: 22 },
      { prompt: 'UPDATE_PLAY_INTENT', sportName: 'Padel', mode: 'FOR_FUN' },
      { prompt: 'REFRESH_YOUR_TIMES' },
    ]);
  });

  // A sentence quotes its payload, so a payload that is not there is a sentence that cannot
  // be written — and inventing the number the question is about is the one thing worse.
  it('drops a prompt whose payload it would have to invent', () => {
    expect(
      toRaisedPrompts(
        shortlist([{ prompt: 'KEEP_THIS_RADIUS' }, { prompt: 'UPDATE_PLAY_INTENT' }]),
        QUOTED,
      ),
    ).toEqual([]);
  });
});
