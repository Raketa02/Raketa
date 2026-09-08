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

  it('draws at most the row’s own width, which is the profile step’s ceiling', () => {
    const seven: readonly SocialTagId[] = [
      'PLAYS_TO_WIN',
      'STAYS_FOR_A_DRINK',
      'QUIET_AND_FOCUSED',
      'HERE_TO_IMPROVE',
      'SHARES_A_LIFT',
      'WARMS_UP_PROPERLY',
      'BOOKS_THE_NEXT_ONE',
    ];
    const row = recordTagRow(seven, undefined);

    expect(row.kind === 'unknown' ? row.tags : []).toHaveLength(6);
  });
});
