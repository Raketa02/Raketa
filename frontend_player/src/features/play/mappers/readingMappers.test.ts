/**
 * The reading's boundary: the deal's mapper over the deal's shape, and the two decisions
 * that are this file's own — a row with no spot is dropped, and a rating in a sport this build
 * cannot name is dropped while its row stands.
 */

import type { Wire } from '@/test-support/transport';

import { toRadarRow, toReading } from './readingMappers';

function response(candidates: readonly Wire['CandidateSchema'][]): Wire['ShortlistResponse'] {
  return {
    search: {
      search_id: '11111111-0000-4000-8000-000000000001',
      at: '2026-09-16T18:00:00Z',
      surface: 'RADAR',
      mode: null,
      ruleset_version: 'ruleset-v1',
      engine_version: 'matchfit-v1',
      optimised_for: 'SEARCHER',
      index_stale: false,
      pool: {
        sport: 'PADEL',
        radius_km_used: 10,
        players_in_range: candidates.length,
        window: 'THIS_WEEK',
        post_gate: true,
        want_to_play_you: 3,
      },
      radius_clamp: false,
      sorts_available: [],
      rung_offers: null,
      my_area_code: 'A+050612+0019938',
    },
    candidates: [...candidates],
  };
}

function row(over: Partial<Wire['CandidateSchema']> = {}): Wire['CandidateSchema'] {
  return {
    player_id: 'aaaaaaaa-0000-4000-8000-000000000001',
    fit: 76,
    distance_km: 1.9,
    bearing_deg: 47,
    ratings: [{ sport: 'PADEL', level: 2.6 }],
    player_card: {
      name: 'Filip N.',
      area_code: 'A+050612+0019938',
      social_tags: ['PLAYS_TO_WIN'],
      level: 2.6,
      band: 'Established',
      range: { low: 2.4, high: 2.8 },
    },
    concerns: [],
    terms: [],
    degraded_terms: [],
    modifiers: [],
    liveness_reasons: [],
    ...over,
  };
}

describe('a reading', () => {
  it('carries the envelope with the deck’s chip on it, and every row with its spot', () => {
    const reading = toReading(response([row()]));

    expect(reading.envelope.searchId).toBe('11111111-0000-4000-8000-000000000001');
    expect(reading.envelope.pool.wantToPlayYou).toBe(3);
    expect(reading.envelope.pool.radiusKmUsed).toBe(10);
    expect(reading.rows).toHaveLength(1);
    expect(reading.rows[0]).toMatchObject({
      playerId: 'aaaaaaaa-0000-4000-8000-000000000001',
      fit: 76,
      distanceKm: 1.9,
      bearingDeg: 47,
      ratings: [{ sport: 'padel', level: 2.6 }],
    });
    expect(reading.rows[0]?.card.name).toBe('Filip N.');
  });

  it('keeps the served order — drawn distance, then id — and sorts nothing', () => {
    const reading = toReading(
      response([
        row({ player_id: 'aaaaaaaa-0000-4000-8000-000000000002', distance_km: 4.8 }),
        row({ player_id: 'aaaaaaaa-0000-4000-8000-000000000001', distance_km: 1.9 }),
      ]),
    );
    expect(reading.rows.map((r) => r.distanceKm)).toEqual([4.8, 1.9]);
  });

  it('drops a row the wire gave no spot — no distance, or no bearing', () => {
    expect(toRadarRow(row({ distance_km: undefined }))).toBeUndefined();
    expect(toRadarRow(row({ bearing_deg: undefined }))).toBeUndefined();
    expect(
      toReading(response([row(), row({ bearing_deg: undefined, player_id: 'x' })])).rows,
    ).toHaveLength(1);
  });

  it('drops a withheld row, which carries no person', () => {
    const withheld = { withheld: true, player_id: 'w', reason: 'BLOCKED' } as never;
    expect(toReading(response([withheld, row()])).rows).toHaveLength(1);
  });

  it('carries every sport they are rated in, in the served order', () => {
    const marek = toRadarRow(
      row({
        ratings: [
          { sport: 'PADEL', level: 2.92 },
          { sport: 'TENNIS', level: 3.4 },
        ],
      }),
    );
    expect(marek?.ratings).toEqual([
      { sport: 'padel', level: 2.92 },
      { sport: 'tennis', level: 3.4 },
    ]);
  });

  it('drops a rating in a sport this build has no name for, and keeps the row', () => {
    const served = toRadarRow(
      row({
        ratings: [
          { sport: 'PADEL', level: 2.92 },
          { sport: 'PICKLEBALL' as never, level: 3.1 },
        ],
      }),
    );
    expect(served?.ratings).toEqual([{ sport: 'padel', level: 2.92 }]);
    expect(served?.card.level).toBe(2.6);
  });

  it('reads a row served without ratings as rated in nothing it can list', () => {
    expect(toRadarRow(row({ ratings: undefined }))?.ratings).toEqual([]);
  });
});
