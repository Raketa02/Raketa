/**
 * **The picture the yes screen draws, on its own** — who is on which side, who is a face and who
 * is an empty seat, and the reader first whatever the wire's order.
 *
 * Pure, because the rule is: the court arrives as every A seat then every B, and a seat is a
 * person only when its occupant has **accepted**. The screen's suite proves the tiles are drawn
 * from this; this proves the fold, which is the half a renderer would only obscure.
 */

import type { DetailSeat } from './challengeDetail';
import { sidesForReader, withOwnFace } from './yesScreen';

const ME = '11111111-2222-4333-8444-555555555555';
const EWA = 'bbbbbbbb-0000-4000-8000-000000000002';
const OLA = 'dddddddd-0000-4000-8000-000000000003';
const KUBA = 'eeeeeeee-0000-4000-8000-000000000004';

const seat = (over: Partial<DetailSeat>): DetailSeat => ({ ...over });

describe('the two sides, reader first', () => {
  it('puts the reader’s side first and the reader first within it, with their seat on side A', () => {
    const sides = sidesForReader(
      [
        seat({ playerId: OLA, nickname: 'Ola.N', answer: 'ACCEPTED' }),
        seat({ playerId: ME, nickname: 'me_', answer: 'ACCEPTED' }),
        seat({ playerId: KUBA, nickname: 'Kuba.W', answer: 'ACCEPTED' }),
        seat({ playerId: EWA, nickname: 'Zofia.B', answer: 'ACCEPTED' }),
      ],
      ME,
    );

    expect(sides?.yours.map((one) => (one.kind === 'person' ? one.playerId : one.kind))).toEqual([
      ME,
      OLA,
    ]);
    expect(sides?.theirs.map((one) => (one.kind === 'person' ? one.playerId : one.kind))).toEqual([
      KUBA,
      EWA,
    ]);
  });

  it('puts the reader’s side first when their seat is on side B', () => {
    const sides = sidesForReader(
      [
        seat({ playerId: EWA, nickname: 'ewa.m', answer: 'ACCEPTED' }),
        seat({ playerId: ME, nickname: 'me_', answer: 'ACCEPTED' }),
      ],
      ME,
    );

    expect(sides?.yours).toEqual([{ kind: 'person', playerId: ME, nickname: 'me_' }]);
    expect(sides?.theirs).toEqual([{ kind: 'person', playerId: EWA, nickname: 'ewa.m' }]);
  });

  it('carries each person’s photograph where the seat card has one', () => {
    const sides = sidesForReader(
      [
        seat({
          playerId: EWA,
          nickname: 'ewa.m',
          answer: 'ACCEPTED',
          card: {
            person: {
              nickname: 'ewa.m',
              photoUrl: 'https://photos.example/ewa',
              areaCode: 'WAW-C',
              level: 2.7,
              band: 'Established',
              range: { low: 2.5, high: 2.9 },
            },
            pairing: { fit: 70, terms: [], degradedTerms: [], concerns: [] },
          },
        }),
        seat({ playerId: ME, nickname: 'me_', answer: 'ACCEPTED' }),
      ],
      ME,
    );

    expect(sides?.theirs[0]).toEqual({
      kind: 'person',
      playerId: EWA,
      nickname: 'ewa.m',
      photoUrl: 'https://photos.example/ewa',
    });
  });
});

/**
 * **A seat is a person only when its occupant has accepted** — the room's own membership rule,
 * so the picture and the row the reader lands on next agree on who is in.
 */
describe('who is a face and who is an empty seat', () => {
  it.each([
    ['still deciding', { playerId: OLA, nickname: 'Ola.N' }],
    ['declined', { playerId: OLA, nickname: 'Ola.N', answer: 'DECLINED' as const }],
    ['lapsed', { playerId: OLA, nickname: 'Ola.N', answer: 'LAPSED' as const }],
    ['left', { playerId: OLA, nickname: 'Ola.N', answer: 'LEFT' as const }],
    ['nobody', {}],
  ])('draws a seat that is %s as an empty seat', (_, other) => {
    const sides = sidesForReader(
      [
        seat({ playerId: ME, nickname: 'me_', answer: 'ACCEPTED' }),
        seat(other),
        seat({ playerId: KUBA, nickname: 'Kuba.W', answer: 'ACCEPTED' }),
        seat({ playerId: EWA, nickname: 'Zofia.B', answer: 'ACCEPTED' }),
      ],
      ME,
    );

    expect(sides?.yours).toEqual([
      { kind: 'person', playerId: ME, nickname: 'me_' },
      { kind: 'empty' },
    ]);
    expect(sides?.theirs).toHaveLength(2);
  });

  it('is nothing for a reader who holds no seat, or one they have not accepted', () => {
    const court = [
      seat({ playerId: EWA, nickname: 'ewa.m', answer: 'ACCEPTED' }),
      seat({ playerId: ME, nickname: 'me_' }),
    ];

    expect(sidesForReader(court, ME)).toBeUndefined();
    expect(sidesForReader(court, KUBA)).toBeUndefined();
  });
});

/** The reader's own face goes on the reader's tile and nowhere else, and nothing where there is none. */
describe('the reader’s own face', () => {
  const sides = {
    yours: [
      { kind: 'person' as const, playerId: ME, nickname: 'me_' },
      { kind: 'person' as const, playerId: OLA, nickname: 'Ola.N' },
    ],
    theirs: [{ kind: 'person' as const, playerId: EWA, nickname: 'ewa.m' }],
  };

  it('is put on the first tile of the reader’s side', () => {
    const drawn = withOwnFace(sides, 'https://photos.example/me');

    expect(drawn.yours[0]).toEqual({
      kind: 'person',
      playerId: ME,
      nickname: 'me_',
      photoUrl: 'https://photos.example/me',
    });
    expect(drawn.yours[1]).toEqual(sides.yours[1]);
    expect(drawn.theirs).toEqual(sides.theirs);
  });

  it('leaves the poster where there is no photograph, or the read did not answer', () => {
    expect(withOwnFace(sides, undefined)).toBe(sides);
  });
});
