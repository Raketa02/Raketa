import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import { recordTagRow } from './tagRow';

const THEIRS: readonly SocialTagId[] = ['PLAYS_TO_WIN', 'STAYS_FOR_A_DRINK'];

describe('the record’s Social tag row', () => {
  it('draws their live tags and claims nothing where no comparison was handed down', () => {
    expect(recordTagRow(THEIRS, undefined)).toEqual({ kind: 'unknown', tags: THEIRS });
  });

  /**
   * The candidate card is a **recorded** answer and its tag terms can stand down entirely, so a
   * row read off the card would be hidden for somebody whose record plainly holds two. The tags
   * are the record's; the caller only ever supplies the register.
   */
  it('draws their tags even where the pairing had none to compare', () => {
    expect(recordTagRow(THEIRS, { kind: 'hidden' })).toEqual({ kind: 'unknown', tags: THEIRS });
  });

  it('tints exactly what the engine matched, and nothing it did not compare', () => {
    const matched: SocialTagOverlap = {
      kind: 'shared',
      tags: [
        { id: 'PLAYS_TO_WIN', shared: true },
        { id: 'QUIET_AND_FOCUSED', shared: false },
      ],
    };

    expect(recordTagRow(THEIRS, matched)).toEqual({
      kind: 'shared',
      tags: [
        { id: 'PLAYS_TO_WIN', shared: true },
        // Published since the search, or in a column that stood down: never compared, so never
        // tinted. *You too* is a judgement the engine made, not a set this client intersected.
        { id: 'STAYS_FOR_A_DRINK', shared: false },
      ],
    });
  });

  /**
   * The one arm that is a claim about **everything**, and it is drawn in the row's place — which
   * is why it outranks having tags to draw.
   */
  it('keeps the engine’s claim about nothing, and never invents one', () => {
    expect(recordTagRow(THEIRS, { kind: 'none-in-common' })).toEqual({ kind: 'none-in-common' });
    expect(recordTagRow([], { kind: 'none-in-common' })).toEqual({ kind: 'none-in-common' });
    expect(recordTagRow([], undefined)).toEqual({ kind: 'hidden' });
  });

  /** ADR-0207 §7: a player holds 2 to 8, so the record draws up to eight — the new ones too. */
  const EIGHT: readonly SocialTagId[] = [
    'STAYS_FOR_A_DRINK',
    'STAYS_FOR_A_COFFEE',
    'KEEPS_IN_TOUCH',
    'PLAYS_TO_WIN',
    'PATIENT_WITH_BEGINNERS',
    'BRINGS_THE_ENERGY',
    'HERE_TO_IMPROVE',
    'NEW_IN_TOWN',
  ];

  it('draws all eight a player may hold, the shared ones tinted', () => {
    expect(recordTagRow(EIGHT, undefined)).toEqual({ kind: 'unknown', tags: EIGHT });

    const matched: SocialTagOverlap = {
      kind: 'shared',
      tags: [
        { id: 'STAYS_FOR_A_COFFEE', shared: true },
        { id: 'NEW_IN_TOWN', shared: true },
      ],
    };
    const row = recordTagRow(EIGHT, matched);

    expect(row.kind === 'shared' ? row.tags : []).toEqual(
      EIGHT.map((id) => ({ id, shared: id === 'STAYS_FOR_A_COFFEE' || id === 'NEW_IN_TOWN' })),
    );
  });

  it('draws at most the row’s own width, which is the profile step’s ceiling', () => {
    const nine: readonly SocialTagId[] = [...EIGHT, 'HAPPY_TO_SHARE_TIPS'];
    const row = recordTagRow(nine, undefined);

    expect(row.kind === 'unknown' ? row.tags : []).toEqual(EIGHT);
  });
});
