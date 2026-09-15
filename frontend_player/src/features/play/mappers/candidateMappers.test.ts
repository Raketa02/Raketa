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

/** The searcher's own coarse area, as `area_code_of` spells one. */
const MY_AREA = 'A+05218+002123';

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
      name: 'Marek Z.',
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
      // The builder's own field: a shortlist and a deal are always the searcher's, and only a
      // hand-seated line-up says otherwise.
      optimisedFor: 'SEARCHER',
      pool: { radiusKmUsed: 12, playersInRange: 7, window: 'THIS_WEEK' },
      radiusClamp: false,
      sortsAvailable: [],
      rungOffers: null,
      rulesetVersion: 'ruleset-v1',
      engineVersion: 'matchfit-v1',
    });
  });

  it('draws the sort row from the server’s own list, dropping a code it cannot read', () => {
    const envelope = toSearchEnvelope(
      response({ sorts_available: ['BEST_FIT', 'STEADIEST' as Wire['SortOption'], 'CLOSEST'] }),
    );

    expect(envelope.sortsAvailable).toEqual(['BEST_FIT', 'CLOSEST']);
  });

  /**
   * The falsifier is `null` against not-null: `null` is *the list cleared five and nobody
   * needed offers*, `[]` is *they were computed and there is nothing left to offer*. A `?? []`
   * anywhere on this path would delete the difference between a long list and a terminal one.
   */
  it('keeps the two empty ladders apart', () => {
    expect(toSearchEnvelope(response({ rung_offers: null })).rungOffers).toBeNull();
    expect(toSearchEnvelope(response({ rung_offers: [] })).rungOffers).toEqual([]);
  });

  it('carries a priced rung whole, and never the widening it would apply', () => {
    const envelope = toSearchEnvelope(
      response({
        rung_offers: [
          {
            rung: 'A',
            ask: 'TIMES',
            candidates_above_floor: 7,
            window: 'WEEKEND',
            slot: { day: 6, part: 'MORNING' },
          },
          {
            rung: 'B',
            ask: 'RADIUS',
            candidates_above_floor: 9,
            window: 'THIS_WEEK',
            radius_km: 22,
          },
        ],
      }),
    );

    expect(envelope.rungOffers).toEqual([
      // The cell crosses to be **drawn** and never to be sent back: the backend reads the
      // widening off the offer it made, and `SearchAsk` has nowhere to put one.
      {
        rung: 'A',
        ask: 'TIMES',
        candidatesAboveFloor: 7,
        window: 'WEEKEND',
        slot: { day: 6, part: 'morning' },
      },
      // A rung never relaxes two asks at once, so a radius rung's cell is a measured `null`
      // rather than a field it happens to be missing.
      {
        rung: 'B',
        ask: 'RADIUS',
        candidatesAboveFloor: 9,
        window: 'THIS_WEEK',
        radiusKm: 22,
        slot: null,
      },
    ]);
  });

  /**
   * The tick is a clause on a control whose count and label are both true without it —
   * `window`'s own answer one field over, and the opposite of a radius rung's, whose whole
   * label *is* the number it would be missing.
   */
  it('keeps a times rung whose cell it cannot read, with nothing to tick', () => {
    const envelope = toSearchEnvelope(
      response({
        rung_offers: [
          { rung: 'A', ask: 'TIMES', candidates_above_floor: 4, window: 'ANY' },
          {
            rung: 'A',
            ask: 'TIMES',
            candidates_above_floor: 4,
            window: 'ANY',
            slot: { day: 8, part: 'MORNING' },
          },
        ],
      }),
    );

    expect(envelope.rungOffers).toEqual([
      { rung: 'A', ask: 'TIMES', candidatesAboveFloor: 4, window: 'ANY', slot: null },
      { rung: 'A', ask: 'TIMES', candidatesAboveFloor: 4, window: 'ANY', slot: null },
    ]);
  });

  /** A radius rung's whole label *is* that number, so there is no sentence left to draw. */
  it('drops a radius rung with no radius, and a rung it cannot name', () => {
    const envelope = toSearchEnvelope(
      response({
        rung_offers: [
          { rung: 'B', ask: 'RADIUS', candidates_above_floor: 9, window: 'THIS_WEEK' },
          { rung: 'D' as Wire['Rung'], ask: 'TIMES', candidates_above_floor: 4, window: 'ANY' },
          {
            rung: 'A',
            ask: 'LEVEL' as Wire['RelaxationAsk'],
            candidates_above_floor: 4,
            window: 'ANY',
          },
        ],
      }),
    );

    expect(envelope.rungOffers).toEqual([]);
  });

  /**
   * The second half of the one comparison a card is licensed to make. It is the area the
   * search **ran on**, so it travels on the envelope rather than being looked up per card.
   */
  it('folds on the searcher’s own area code', () => {
    expect(toSearchEnvelope(response({ my_area_code: MY_AREA })).myAreaCode).toBe(MY_AREA);
  });

  /**
   * A search recorded before the backend kept one carries no code, and searches are kept for
   * ever — so an absent value is the honest spelling of it, where a sentinel string would
   * quietly mean *never in your area* (`domain/candidate`).
   */
  it('sets no area code where the search recorded none', () => {
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

    expect(candidate.card.name).toBe('Marek Z.');
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

  /** The record block's three fields, all of which a card draws since #312. */
  it('carries the published Player Score, which is what *Most reliable* orders by', () => {
    const card = { ...row().player_card, player_score: 74 };

    expect(toCandidate(row({ player_card: card })).card.playerScore).toBe(74);
  });

  /** Omitted rather than zero — what lets *Most reliable* sort a player with no record last. */
  it('omits the Player Score where the platform has watched nothing', () => {
    expect(toCandidate(row()).card).not.toHaveProperty('playerScore');
  });

  it('carries the counted games and the run of form, oldest to newest', () => {
    const card: Wire['PlayerCardSchema'] = {
      ...row().player_card,
      counted_games: 29,
      last_five: ['WIN', 'LOSS', 'WIN'],
    };
    const drawn = toCandidate(row({ player_card: card })).card;

    expect(drawn.countedGames).toBe(29);
    // In the order served. Nothing on this side sorts, reverses or pads to five: the length
    // is the statement, and the card draws the gap.
    expect(drawn.lastFive).toEqual(['WIN', 'LOSS', 'WIN']);
  });

  it('omits both of them rather than sending a nought and an empty run', () => {
    // Absence has one spelling on this card. *Nought games* and *no record* would be one
    // absence in two, and the block is hidden rather than drawn with a zero in it.
    const drawn = toCandidate(row()).card;

    expect(drawn).not.toHaveProperty('countedGames');
    expect(drawn).not.toHaveProperty('lastFive');
  });

  /**
   * The one narrowing that takes the **whole field** with it, and the reason it is not §3's
   * ordinary drop.
   *
   * The run's length is itself a statement — five squares means five counted results — so an
   * outcome this build cannot read has nowhere to go: dropped it shortens the run and claims a
   * game fewer than the platform counted, and kept as a gap it asks the card to draw a third
   * kind of square nobody has designed. So the block is hidden, and `counted_games` beside it
   * goes on printing: the honesty figure survives a run this build can only half read.
   */
  it('omits the whole run where one outcome is a code this build cannot read', () => {
    const card: Wire['PlayerCardSchema'] = {
      ...row().player_card,
      counted_games: 29,
      // The eight-month-old phone, in one value: a third outcome the platform added and this
      // build has never seen.
      last_five: ['WIN', 'RETIRED' as Wire['GameResult'], 'LOSS'],
    };
    const drawn = toCandidate(row({ player_card: card })).card;

    expect(drawn).not.toHaveProperty('lastFive');
    expect(drawn.countedGames).toBe(29);
  });

  /**
   * `at_stake` sits on the candidate rather than on the card, which is `distance_km`'s
   * placement for `distance_km`'s reason: it is a fact about a **pair**.
   */
  it('carries what a counted game would move, both figures as served', () => {
    const drawn = toCandidate(row({ at_stake: { win_delta: 0.08, loss_delta: -0.05 } }));

    expect(drawn.atStake).toEqual({ winDelta: 0.08, lossDelta: -0.05 });
  });

  it('omits it in for fun, where a counted result is meaningless rather than unavailable', () => {
    expect(toCandidate(row())).not.toHaveProperty('atStake');
  });

  it('omits the photo URL where there is no photograph, so the poster is drawn', () => {
    const card = { ...row().player_card, photo_url: undefined };

    expect(toCandidate(row({ player_card: card })).card).not.toHaveProperty('photoUrl');
  });

  it('carries the verdict where the check reached one', () => {
    const card = { ...row().player_card, review: 'allowed' as const };

    expect(toCandidate(row({ player_card: card })).card.photoReview).toBe('allowed');
  });

  it('carries a flagged verdict too — it is the card that declines to draw it', () => {
    // The narrowing is a wire concern and the drawing is `domain/onCourtMark`'s. Folding
    // `flagged` to absent here would put a product rule in a mapper and take the code away
    // from the one place a future surface could legitimately read it.
    const card = { ...row().player_card, review: 'flagged' as const };

    expect(toCandidate(row({ player_card: card })).card.photoReview).toBe('flagged');
  });

  it('omits it where nobody looked, which is the state that draws no mark', () => {
    expect(toCandidate(row()).card).not.toHaveProperty('photoReview');
  });

  it('omits it on a verdict this build has never seen, and that is the safe fold', () => {
    // Through `unknown`, because the generated union is exactly the set of verdicts this
    // build knows and the case being tested is the one it does not. A code minted after this
    // build shipped could be anything, including a refusal — reading it as a pass is the one
    // reading that could put a mark on a photograph the platform had doubts about, so the
    // unreadable verdict and *nobody looked* collapse to one answer.
    const card = {
      ...row().player_card,
      review: 'quarantined',
    } as unknown as Wire['PlayerCardSchema'];

    expect(toCandidate(row({ player_card: card })).card).not.toHaveProperty('photoReview');
  });

  it('drops a social tag this build has no words for', () => {
    const card = { ...row().player_card, social_tags: ['PLAYS_TO_WIN', 'DOES_THE_CROSSWORD'] };

    expect(toCandidate(row({ player_card: card })).card.socialTags).toEqual(['PLAYS_TO_WIN']);
  });

  /**
   * The one narrowing that is not free, and the bit that keeps it honest.
   *
   * Every tag list is narrowed against the nineteen ids this build has words for. Everywhere
   * else that is a sentence going unwritten; on the competitive card's tag row it would be an
   * empty `matched` licensing the amber *No tags in common*, which is a claim
   * ([#311](https://github.com/Raketa02/Raketa/issues/311)).
   */
  describe('a match this build has no words for', () => {
    const tagTerm = (matched: string[]): Wire['ScoredTermSchema'] =>
      ({
        term: 'PLAYING_STYLE',
        weight: 12,
        value: 0.5,
        contribution: 6,
        evidence: { kind: 'playing_style', matched, complementary: [], clashing: [] },
      }) as Wire['ScoredTermSchema'];

    const relationships = (matched: string[]) =>
      toCandidate(row({ terms: [tagTerm(matched)] })).terms[0]?.evidence;

    it('is dropped from the list, exactly as every other tag id is', () => {
      expect(relationships(['PLAYS_TO_WIN', 'DOES_THE_CROSSWORD'])).toMatchObject({
        matched: ['PLAYS_TO_WIN'],
      });
    });

    it('says so, so the card never reports an overlap it narrowed away as none', () => {
      expect(relationships(['DOES_THE_CROSSWORD'])).toMatchObject({
        matched: [],
        matchedInFull: false,
      });
    });

    it('leaves the bit true where nothing was narrowed, including an empty answer', () => {
      expect(relationships(['PLAYS_TO_WIN'])).toMatchObject({ matchedInFull: true });
      expect(relationships([])).toMatchObject({ matchedInFull: true });
    });
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
    expect(list.candidates[0]?.card.name).toBe('Marek Z.');
  });
});
