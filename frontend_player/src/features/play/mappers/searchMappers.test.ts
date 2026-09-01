import type { Wire } from '@/test-support/transport';

import {
  toOriginSearch,
  toPlayersInRange,
  toRaisedPrompts,
  toRunSearchRequest,
} from './searchMappers';

const TUESDAY_EVENING = { day: 2, part: 'evening' } as const;

const ORIGIN = {
  sport: 'padel',
  mode: 'COMPETITIVE',
  week: [TUESDAY_EVENING],
} as const;

/** The profile's own week — four cells, which is `KEEP_THESE_TIMES`'s second number. */
const PROFILE_WEEK = [
  { day: 1, part: 'evening' },
  { day: 2, part: 'evening' },
  { day: 4, part: 'morning' },
  { day: 6, part: 'morning' },
] as const;

const QUOTED = { sportName: 'Padel', profileWeek: PROFILE_WEEK };

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

describe('the count the latch prints', () => {
  /**
   * `players_in_range` and nothing else off the pool: the searching latch prints one number,
   * and a reading with fields nobody draws would be a contract nobody is checking.
   */
  it('is the response’s own post-gate count', () => {
    expect(toPlayersInRange(shortlist())).toBe(7);
  });
});

describe('the questions a search raises', () => {
  it('raises none where the response carries none', () => {
    expect(toRaisedPrompts(shortlist(), QUOTED)).toEqual([]);
  });

  /**
   * The week the search ran on arrives as the **joined codes the stream stores**, which is the
   * one shape `AvailabilitySlotResource` exists to spare a client — so it is split here and
   * the sheet is handed cells it can draw rather than strings it would have to parse.
   */
  it('lifts the week the search ran on, beside the one on the profile', () => {
    const raised = toRaisedPrompts(
      shortlist([{ prompt: 'KEEP_THESE_TIMES', slots: ['2:EVENING', '6:MORNING'] }]),
      QUOTED,
    );

    expect(raised).toEqual([
      {
        prompt: 'KEEP_THESE_TIMES',
        week: [
          { day: 2, part: 'evening' },
          { day: 6, part: 'morning' },
        ],
        profileWeek: PROFILE_WEEK,
      },
    ]);
  });

  /** A code this build cannot read is dropped, exactly as an eighth day is on the read. */
  it('drops a slot code it cannot read, from the drawing and the count alike', () => {
    const raised = toRaisedPrompts(
      shortlist([{ prompt: 'KEEP_THESE_TIMES', slots: ['2:EVENING', '9:EVENING', '3:SIESTA'] }]),
      QUOTED,
    );

    expect(raised).toEqual([
      {
        prompt: 'KEEP_THESE_TIMES',
        week: [{ day: 2, part: 'evening' }],
        profileWeek: PROFILE_WEEK,
      },
    ]);
  });

  // `()` is a cleared week and is a real offer; `None` is *not this prompt*.
  it('offers to keep a cleared week', () => {
    expect(toRaisedPrompts(shortlist([{ prompt: 'KEEP_THESE_TIMES', slots: [] }]), QUOTED)).toEqual(
      [{ prompt: 'KEEP_THESE_TIMES', week: [], profileWeek: PROFILE_WEEK }],
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
