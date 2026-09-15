/**
 * **The tag row's four answers**, and the three spellings of absence between them.
 *
 * The two the ticket names are *they share nothing* and *the platform does not know*, and the
 * whole point is that they are different sentences. The third is this build's own: the platform
 * matched something it has no words for, which is neither — it must not tint (there is nothing
 * to tint) and it must not say *No tags in common*, because that is a claim it would be making
 * out of its own ignorance.
 */

import type { Candidate } from './candidate';
import type { ScoredTerm, TagRelationships } from './evidence';
import { socialTagOverlap } from './socialTagOverlap';
import type { Term } from './vocabulary';

const THEIRS = ['PLAYS_TO_WIN', 'STAYS_FOR_A_DRINK', 'QUIET_AND_FOCUSED'] as const;

function tagTerm(
  term: Extract<Term, 'PLAYING_STYLE' | 'SOCIAL_VIBE'>,
  over: Partial<TagRelationships> = {},
): ScoredTerm {
  const relationships: TagRelationships = {
    matched: [],
    matchedInFull: true,
    complementary: [],
    clashing: [],
    ...over,
  };
  return {
    term,
    weight: 10,
    value: 0.5,
    contribution: 5,
    evidence:
      term === 'PLAYING_STYLE'
        ? { kind: 'playing_style', ...relationships }
        : { kind: 'social_vibe', ...relationships },
  };
}

function candidate(over: Partial<Candidate> = {}): Candidate {
  return {
    playerId: 'p1',
    fit: 78,
    card: {
      nickname: 'marek',
      areaCode: 'A+050612+0019938',
      socialTags: [...THEIRS],
      level: 2.8,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    terms: [],
    concerns: [],
    livenessReasons: [],
    degradedTerms: [],
    modifiers: [],
    ...over,
  };
}

describe('the platform compared, and something matched', () => {
  it('draws every tag they published and marks the shared ones', () => {
    const row = socialTagOverlap(
      candidate({ terms: [tagTerm('PLAYING_STYLE', { matched: ['PLAYS_TO_WIN'] })] }),
    );

    expect(row).toEqual({
      kind: 'shared',
      tags: [
        { id: 'PLAYS_TO_WIN', shared: true },
        { id: 'STAYS_FOR_A_DRINK', shared: false },
        { id: 'QUIET_AND_FOCUSED', shared: false },
      ],
    });
  });

  it('keeps the order the server served, and never the order of the match', () => {
    const row = socialTagOverlap(
      candidate({ terms: [tagTerm('SOCIAL_VIBE', { matched: ['QUIET_AND_FOCUSED'] })] }),
    );

    expect(row.kind === 'shared' ? row.tags.map((tag) => tag.id) : []).toEqual([...THEIRS]);
  });

  it('takes the union across both tag terms, which are two columns of one matrix', () => {
    const row = socialTagOverlap(
      candidate({
        terms: [
          tagTerm('PLAYING_STYLE', { matched: ['PLAYS_TO_WIN'] }),
          tagTerm('SOCIAL_VIBE', { matched: ['STAYS_FOR_A_DRINK'] }),
        ],
      }),
    );

    expect(
      row.kind === 'shared' ? row.tags.filter((tag) => tag.shared).map((t) => t.id) : [],
    ).toEqual(['PLAYS_TO_WIN', 'STAYS_FOR_A_DRINK']);
  });

  /** A pair the product claims fit together is a different relationship — §7's, and prose. */
  it('tints nothing off a complementary or clashing pair', () => {
    const row = socialTagOverlap(
      candidate({
        terms: [
          tagTerm('PLAYING_STYLE', {
            complementary: [{ a: 'PLAYS_TO_WIN', b: 'QUIET_AND_FOCUSED' }],
            clashing: [{ a: 'STAYS_FOR_A_DRINK', b: 'QUIET_AND_FOCUSED' }],
          }),
          tagTerm('SOCIAL_VIBE'),
        ],
      }),
    );

    expect(row.kind).toBe('none-in-common');
  });

  it('drops an id this build has no words for, because the mapper already did', () => {
    // §3's drop reaching this rule as an absence rather than as a blank chip: the mapper
    // narrows `social_tags` against the same table the labels come from.
    const row = socialTagOverlap(
      candidate({
        card: { ...candidate().card, socialTags: ['PLAYS_TO_WIN'] },
        terms: [tagTerm('PLAYING_STYLE', { matched: ['PLAYS_TO_WIN'] })],
      }),
    );

    expect(row.kind === 'shared' ? row.tags : []).toEqual([{ id: 'PLAYS_TO_WIN', shared: true }]);
  });
});

describe('the platform compared, and nothing matched', () => {
  it('is the amber line, which stands in the row’s place', () => {
    const both = [tagTerm('PLAYING_STYLE'), tagTerm('SOCIAL_VIBE')];

    expect(socialTagOverlap(candidate({ terms: both }))).toEqual({ kind: 'none-in-common' });
  });

  /**
   * The claim needs both columns and a match needs only one, which is the asymmetry the rule is
   * built on: a `matched` list is a positive fact, and *No tags in common* is a claim about
   * everything. A half-compared candidate has not earned the second.
   */
  it('is not the amber line when only one of the two columns fired', () => {
    expect(socialTagOverlap(candidate({ terms: [tagTerm('SOCIAL_VIBE')] }))).toEqual({
      kind: 'unknown',
      tags: [...THEIRS],
    });
  });

  it('still marks a match found by one column alone, because that is a fact and not a claim', () => {
    const row = socialTagOverlap(
      candidate({ terms: [tagTerm('SOCIAL_VIBE', { matched: ['STAYS_FOR_A_DRINK'] })] }),
    );

    expect(row.kind === 'shared' ? row.tags.filter((t) => t.shared).map((t) => t.id) : []).toEqual([
      'STAYS_FOR_A_DRINK',
    ]);
  });
});

describe('the platform did not compare', () => {
  it('draws their tags untinted, and says nothing about the overlap', () => {
    expect(socialTagOverlap(candidate())).toEqual({ kind: 'unknown', tags: [...THEIRS] });
  });

  it('is hidden rather than blank when they published nothing this build can draw', () => {
    expect(socialTagOverlap(candidate({ card: { ...candidate().card, socialTags: [] } }))).toEqual({
      kind: 'hidden',
    });
  });

  /** A term fired but its evidence is a variant this build cannot read — §3, one level up. */
  it('does not count a term whose evidence it cannot read as a comparison', () => {
    const unreadable: ScoredTerm = { ...tagTerm('PLAYING_STYLE'), evidence: null };

    expect(socialTagOverlap(candidate({ terms: [unreadable] }))).toEqual({
      kind: 'unknown',
      tags: [...THEIRS],
    });
  });
});

describe('the platform matched something this build cannot name', () => {
  /**
   * The third spelling, and the reason `matchedInFull` exists. `matched` is narrowed at the
   * mapper against the same nineteen the labels come from, so a build that has not been
   * updated sees an empty list where the platform found an overlap.
   */
  it('never says No tags in common, because there is one and it cannot name it', () => {
    // Both columns fired, so the amber line is otherwise earned — the bit is the only thing
    // standing between this card and a false claim.
    const row = socialTagOverlap(
      candidate({
        terms: [tagTerm('PLAYING_STYLE', { matchedInFull: false }), tagTerm('SOCIAL_VIBE')],
      }),
    );

    expect(row).toEqual({ kind: 'unknown', tags: [...THEIRS] });
  });

  it('still marks the matches it can read when only some were narrowed away', () => {
    const row = socialTagOverlap(
      candidate({
        terms: [tagTerm('PLAYING_STYLE', { matched: ['PLAYS_TO_WIN'], matchedInFull: false })],
      }),
    );

    expect(
      row.kind === 'shared' ? row.tags.filter((tag) => tag.shared).map((t) => t.id) : [],
    ).toEqual(['PLAYS_TO_WIN']);
  });
});

describe('the cap', () => {
  it('draws six and no more, which is the profile step’s own ceiling', () => {
    const seven = [
      ...THEIRS,
      'LAUGHS_OFF_MISTAKES',
      'WARMS_UP_PROPERLY',
      'HERE_TO_IMPROVE',
      'SHARES_A_LIFT',
    ] as const;
    const row = socialTagOverlap(
      candidate({ card: { ...candidate().card, socialTags: [...seven] } }),
    );

    expect(row.kind === 'unknown' ? row.tags : []).toHaveLength(6);
  });

  /**
   * **The deck's order runs before the cap** (ADR-0169 §7): a shared tag published seventh is
   * the one a served-order cap would cut off, and it is exactly the one the deck wants first.
   * In the served order the same seventh is cut — the row is *what they published*.
   */
  it('puts a shared tag first before capping, when asked for the deck’s order', () => {
    const seven = [
      ...THEIRS,
      'LAUGHS_OFF_MISTAKES',
      'WARMS_UP_PROPERLY',
      'HERE_TO_IMPROVE',
      'SHARES_A_LIFT',
    ] as const;
    const seventhShared = candidate({
      card: { ...candidate().card, socialTags: [...seven] },
      terms: [tagTerm('SOCIAL_VIBE', { matched: ['SHARES_A_LIFT'] })],
    });

    const deck = socialTagOverlap(seventhShared, 'shared-first');
    expect(deck.kind === 'shared' ? deck.tags.map((tag) => tag.id) : []).toEqual([
      'SHARES_A_LIFT',
      ...seven.slice(0, 5),
    ]);
    expect(deck.kind === 'shared' ? deck.tags[0]?.shared : false).toBe(true);

    const served = socialTagOverlap(seventhShared);
    expect(served.kind === 'shared' ? served.tags.map((tag) => tag.id) : []).toEqual([
      ...seven.slice(0, 6),
    ]);
  });
});
