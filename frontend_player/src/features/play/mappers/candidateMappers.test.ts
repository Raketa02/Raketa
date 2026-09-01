/**
 * The candidate boundary, and the four narrowings §3 decides separately.
 *
 * A generated union says a served code is always one this build knows, which is true of the
 * document these types came from and false of a phone that has not been updated in eight
 * months. So the assertions here are mostly about **what an unknown code costs**, and the
 * costs deliberately differ: a tag is dropped, a term is counted, a degraded reason is kept as
 * a gap. Getting one of those wrong is a list that is silently shorter than the answer it
 * describes, which is the failure ADR-0106 §6 exists to prevent.
 */

import type { Wire } from '@/test-support/transport';

import { toCandidate, toRankedList, toSearchEnvelope } from './candidateMappers';

function response(over: Partial<Wire['ShortlistResponse']['search']> = {}) {
  return {
    search: {
      search_id: '11111111-0000-4000-8000-000000000001',
      at: '2026-09-01T18:00:00Z',
      surface: 'DECK',
      mode: null,
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
      sorts_available: [],
      rung_offers: null,
      ...over,
    },
    candidates: [],
  } as Wire['ShortlistResponse'];
}

function row(over: Partial<Wire['CandidateSchema']> = {}): Wire['CandidateSchema'] {
  return {
    player_id: 'aaaaaaaa-0000-4000-8000-000000000001',
    fit: 78,
    distance_km: 4,
    player_card: {
      nickname: 'Marek Z.',
      photo_url: 'https://photos.example/marek?sig=abc',
      area_code: 'A+050612+0019938',
      social_tags: ['PLAYS_TO_WIN'],
      level: 2.83,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    concerns: [],
    terms: [],
    degraded_terms: [],
    modifiers: [],
    liveness_reasons: [],
    ...over,
  };
}

const OVERLAP: Wire['ScoredTermSchema'] = {
  term: 'AVAILABILITY_OVERLAP',
  weight: 16,
  value: 0.5,
  contribution: 8,
  evidence: {
    kind: 'availability_overlap',
    shared_count: 3,
    next_slot: { day: 2, part: 'EVENING' },
  },
};

describe('the envelope', () => {
  it('carries the pool, the clamp and the two version stamps', () => {
    expect(toSearchEnvelope(response())).toEqual({
      searchId: '11111111-0000-4000-8000-000000000001',
      mode: null,
      pool: { radiusKmUsed: 12, playersInRange: 7, window: 'THIS_WEEK' },
      radiusClamp: false,
      rulesetVersion: 'ruleset-v1',
      engineVersion: 'matchfit-v1',
    });
  });

  /**
   * No route serves the searcher their own coarse area, so there is nothing to fold on — and
   * an absent value is the honest spelling of that, where a sentinel string would quietly
   * mean *never in your area* (`domain/candidate`).
   */
  it('sets no area code of the searcher’s, because nothing serves one', () => {
    expect(toSearchEnvelope(response())).not.toHaveProperty('myAreaCode');
  });

  it('reads a mode it does not know as no mode at all', () => {
    expect(toSearchEnvelope(response({ mode: 'DOUBLES_ONLY' as never })).mode).toBeNull();
  });

  it('drops a window it cannot read, leaving the count and the radius to say the rest', () => {
    const pool = { ...response().search.pool, window: 'FORTNIGHT' as never };

    expect(toSearchEnvelope(response({ pool })).pool.window).toBeNull();
  });
});

describe('the candidate', () => {
  it('renames the wire’s fields and keeps the order it was given', () => {
    const candidate = toCandidate(row({ terms: [OVERLAP] }));

    expect(candidate.card.nickname).toBe('Marek Z.');
    expect(candidate.terms[0]?.evidence).toEqual({
      kind: 'availability_overlap',
      sharedCount: 3,
      nextSlot: { day: 2, part: 'evening' },
    });
  });

  /** Omitted rather than zero — what lets *Closest* sort a stood-down row last, not first. */
  it('omits the distance where the term stood down', () => {
    expect(toCandidate(row({ distance_km: undefined }))).not.toHaveProperty('distanceKm');
  });

  it('omits the photo URL where there is no photograph, so the poster is drawn', () => {
    const card = { ...row().player_card, photo_url: undefined };

    expect(toCandidate(row({ player_card: card })).card).not.toHaveProperty('photoUrl');
  });

  it('drops a social tag this build has no words for', () => {
    const card = { ...row().player_card, social_tags: ['PLAYS_TO_WIN', 'DOES_THE_CROSSWORD'] };

    expect(toCandidate(row({ player_card: card })).card.socialTags).toEqual(['PLAYS_TO_WIN']);
  });

  it('drops a liveness reason it cannot read — a card shows a few of many', () => {
    const candidate = toCandidate(
      row({ liveness_reasons: ['RECENT_ACTIVITY', 'PLAYS_ON_TUESDAYS' as never] }),
    );

    // Dropped rather than gapped: the sheet draws every one it holds, and states no total
    // one of them belongs to.
    expect(candidate.livenessReasons).toEqual(['RECENT_ACTIVITY']);
  });
});

describe('a code this build has never seen', () => {
  /**
   * A scored row is **kept**, and the gap lands in place. Dropping it would move its
   * contribution into the sheet's derived `applied`, where it would read as an adjustment the
   * engine never made — #233 §4's own objection, *"a wrong number that looks like a plausible
   * one"*.
   */
  it('keeps a scored term it cannot name, with the three numbers standing', () => {
    const unknown = { ...OVERLAP, term: 'SENSE_OF_HUMOUR' as never };
    const candidate = toCandidate(row({ terms: [OVERLAP, unknown] }));

    expect(candidate.terms).toHaveLength(2);
    expect(candidate.terms[1]).toMatchObject({
      term: null,
      weight: 16,
      value: 0.5,
      contribution: 8,
    });
    // Its evidence is perfectly readable, so only the name is missing.
    expect(candidate.terms[1]?.evidence).not.toBeNull();
  });

  it('keeps a row whose evidence variant it has no renderer for, and names the term', () => {
    const ninth = { ...OVERLAP, evidence: { kind: 'star_sign', sign: 'libra' } as never };
    const candidate = toCandidate(row({ terms: [ninth] }));

    expect(candidate.terms[0]).toMatchObject({
      term: 'AVAILABILITY_OVERLAP',
      contribution: 8,
      evidence: null,
    });
  });

  /**
   * A stood-down term is kept for the same reason in a different register: the not-counted
   * block **is** the renormalisation basis, so a line that vanished would make the sheet's own
   * account of what did not count shorter than the answer it describes.
   */
  it('keeps a stood-down term whose reason it cannot read', () => {
    const candidate = toCandidate(
      row({ degraded_terms: [{ term: 'RELIABILITY', reason: 'ASLEEP' as never }] }),
    );

    expect(candidate.degradedTerms).toEqual([{ term: 'RELIABILITY', reason: null }]);
  });

  it('keeps a stood-down term whose *term* it cannot read', () => {
    const candidate = toCandidate(
      row({ degraded_terms: [{ term: 'PUNCTUALITY' as never, reason: 'NOTHING_FROM_THEM' }] }),
    );

    expect(candidate.degradedTerms).toEqual([{ term: null, reason: 'NOTHING_FROM_THEM' }]);
  });

  /**
   * A concern is joined back to a row **by its term**, so one this build cannot name could not
   * be marked in place even if it were kept — and no screen states a total it belongs to.
   */
  it('drops a concern it cannot name, which is a selection rather than a total', () => {
    const candidate = toCandidate(
      row({ concerns: [{ term: 'DISTANCE' }, { term: 'PUNCTUALITY' as never }] }),
    );

    expect(candidate.concerns).toEqual(['DISTANCE']);
  });

  it('drops a modifier it cannot name, because nothing sums that list', () => {
    const candidate = toCandidate(
      row({
        modifiers: [
          { code: 'CALIBRATION_VALUE', points: 3 },
          { code: 'GOOD_HAIR' as never, points: 2 },
        ],
      }),
    );

    expect(candidate.modifiers).toEqual([{ code: 'CALIBRATION_VALUE', points: 3 }]);
  });
});

describe('a withheld row', () => {
  /**
   * It carries no person, so it cannot become a candidate — and this is **not** the
   * out-of-date case: this build read the row perfectly, and what changed is that the product
   * will no longer show it. Stating the fact is the court's job, derived as a set difference
   * against the seats a line-up holds; a fresh deal never carries one.
   */
  it('is dropped, because there is no person on it to draw', () => {
    const list = toRankedList({
      ...response(),
      candidates: [row(), { withheld: true }],
    });

    expect(list.candidates).toHaveLength(1);
    expect(list.candidates[0]?.card.nickname).toBe('Marek Z.');
  });
});
