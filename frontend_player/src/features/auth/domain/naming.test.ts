/**
 * **Named** — holding a nickname — and the account that runs a club's groups, which the step asks
 * in words of its own (ADR-0199 §3), with no renderer and no network.
 */

import { named, runsAClub } from './naming';

const ADMINISTERS_OGRODY = {
  actsAsPlayer: true,
  administers: [{ clubId: 'club-ogrody', clubName: 'Ogrody 33' }],
};
const PLAYS_ONLY = { actsAsPlayer: true, administers: [] };

describe('named', () => {
  it('is holding a nickname', () => {
    expect(named({ nickname: 'ania.k' })).toBe(true);
  });

  it('is not an account sign-up created, which holds none until the naming', () => {
    expect(named({})).toBe(false);
  });
});

describe('an account that runs a club’s groups — the sign of one an Invitation opened', () => {
  // The club typed a name for its Administrator, and it stays the Administrator's: the account
  // holds no player name, so what tells the step who this is is the club whose groups it runs.
  it('is one that administers a club', () => {
    expect(runsAClub({ profiles: ADMINISTERS_OGRODY })).toBe(true);
  });

  it('is not an account that only plays', () => {
    expect(runsAClub({ profiles: PLAYS_ONLY })).toBe(false);
  });
});
