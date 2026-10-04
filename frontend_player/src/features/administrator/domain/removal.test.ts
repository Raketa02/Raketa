/**
 * Where an account goes once its club has removed it as an Administrator — with no renderer and no
 * network (PRD #500 story 136, ADR-0185 §3).
 */

import { afterRemoval } from './removal';

const OGRODY = { clubId: 'c0000000-0000-4000-8000-000000000033', clubName: 'Ogrody 33' };
const BONARKA = { clubId: 'c0000000-0000-4000-8000-000000000044', clubName: 'Bonarka Arena' };

describe('after a removal', () => {
  it('signs out an account that held nothing else', () => {
    expect(afterRemoval({ actsAsPlayer: false, administers: [OGRODY] }, OGRODY.clubId)).toEqual({
      kind: 'sign-out',
    });
  });

  it('signs it out whether or not the profile read has caught up with the removal', () => {
    expect(afterRemoval({ actsAsPlayer: false, administers: [] }, OGRODY.clubId)).toEqual({
      kind: 'sign-out',
    });
  });

  it('moves an account that also plays to its player side', () => {
    expect(afterRemoval({ actsAsPlayer: true, administers: [OGRODY] }, OGRODY.clubId)).toEqual({
      kind: 'player',
    });
  });

  it('moves an account that runs another club’s groups to that club’s area', () => {
    expect(
      afterRemoval({ actsAsPlayer: false, administers: [OGRODY, BONARKA] }, OGRODY.clubId),
    ).toEqual({ kind: 'administrator', clubId: BONARKA.clubId });
  });

  it('prefers the player side to another club, as a launch does', () => {
    expect(
      afterRemoval({ actsAsPlayer: true, administers: [OGRODY, BONARKA] }, OGRODY.clubId),
    ).toEqual({ kind: 'player' });
  });
});
