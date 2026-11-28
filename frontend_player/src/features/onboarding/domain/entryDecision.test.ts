/**
 * The entry gate's rule, with no renderer and no network.
 *
 * These cases are the whole of "where does a player belong on launch", and each one is a
 * decision someone could plausibly get backwards. **Ratings and an unfinished run are not among
 * its inputs** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §1, §5, [#730](https://github.com/Rakieta02/Rakieta/issues/730)): onboarding is a nickname and a
 * profile, and a level is asked where play begins — so neither can route anywhere, by
 * construction.
 */

import { entryDestination, type EntryInput } from './entryDecision';

/** What every signed-up account holds: it acts as a player and runs no club's groups. */
const A_PLAYER: EntryInput['profiles'] = { actsAsPlayer: true, administers: [] };

const OGRODY = { clubId: 'c0000000-0000-4000-8000-000000000001', clubName: 'Ogrody 33' };
const BONARKA = { clubId: 'c0000000-0000-4000-8000-000000000002', clubName: 'Bonarka Arena' };

describe('where a player belongs on launch', () => {
  it('sends a named player with a Player profile into the app — rated in nothing or not', () => {
    expect(entryDestination({ named: true, hasPlayerProfile: true, profiles: A_PLAYER })).toEqual({
      kind: 'app',
    });
  });

  it('sends a named player with no Player profile to the profile steps, from their first', () => {
    // The account sign-up and the naming leave behind: *What kind of player are you?* is next,
    // with no questionnaire, no values screen and no summary in front of it.
    expect(entryDestination({ named: true, hasPlayerProfile: false, profiles: A_PLAYER })).toEqual({
      kind: 'social-steps',
    });
  });
});

describe('an account with no nickname yet', () => {
  it('is sent to the naming step, ahead of the profile steps', () => {
    expect(entryDestination({ named: false, hasPlayerProfile: false, profiles: A_PLAYER })).toEqual(
      { kind: 'naming' },
    );
  });

  it('is sent to the naming step ahead of the app, whatever else they hold', () => {
    // An account the flow cannot produce — set up, but unnamed — is still routed, and to the
    // step it owes: a shape the gate does not route is a loop.
    expect(entryDestination({ named: false, hasPlayerProfile: true, profiles: A_PLAYER })).toEqual({
      kind: 'naming',
    });
  });
});

/**
 * **An account that only runs a club's groups has not asked to play**
 * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §1–§3), so it is sent to its club's administrator area and never into onboarding — whatever its
 * nickname or its profile say.
 */
describe('an account that holds only administrator profiles', () => {
  const ADMINISTRATOR_ONLY: EntryInput['profiles'] = {
    actsAsPlayer: false,
    administers: [OGRODY],
  };

  it('is sent to the administrator area of its club', () => {
    expect(
      entryDestination({ named: true, hasPlayerProfile: false, profiles: ADMINISTRATOR_ONLY }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('is sent there ahead of the naming step, and never into onboarding', () => {
    // An account an Invitation opened: the club typed a name, and nobody chose a nickname.
    expect(
      entryDestination({ named: false, hasPlayerProfile: false, profiles: ADMINISTRATOR_ONLY }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('opens on the first club it administers, in the server’s order', () => {
    expect(
      entryDestination({
        named: true,
        hasPlayerProfile: false,
        profiles: { actsAsPlayer: false, administers: [BONARKA, OGRODY] },
      }),
    ).toEqual({ kind: 'administrator', clubId: BONARKA.clubId });
  });

  // Two profiles open in Player by default (ADR-0185 §3).
  it('does not take an account that also plays out of the player’s app', () => {
    expect(
      entryDestination({
        named: true,
        hasPlayerProfile: true,
        profiles: { actsAsPlayer: true, administers: [OGRODY] },
      }),
    ).toEqual({ kind: 'app' });
  });
});

/**
 * **An account with no profile at all is offered the player setup, from the Adult attestation**
 * (ADR-0185 §3, [#517](https://github.com/Rakieta02/Rakieta/issues/517)). The only way to be one is
 * an administrator-only account whose club removed it. Signing in again must never be a dead end,
 * so it takes *Start playing*'s steps from the gate — and the first is the attestation, which it
 * has never given and which comes ahead of anything player-side, the naming included (§5).
 */
describe('an account that holds no profile at all', () => {
  const NO_PROFILE: EntryInput['profiles'] = { actsAsPlayer: false, administers: [] };

  it('is sent to Start playing’s first step, ahead of the naming', () => {
    expect(
      entryDestination({ named: false, hasPlayerProfile: false, profiles: NO_PROFILE }),
    ).toEqual({ kind: 'start-playing' });
  });
});

/**
 * **Named is holding a nickname** (ADR-0199 §3–§4). An account an Invitation opened holds none;
 * once it has attested it acts as a player, and the naming step is where it goes first.
 */
describe('an administrator who has just started playing', () => {
  it('is sent to the naming step, holding no nickname yet', () => {
    expect(
      entryDestination({
        named: false,
        hasPlayerProfile: false,
        profiles: { actsAsPlayer: true, administers: [OGRODY] },
      }),
    ).toEqual({ kind: 'naming' });
  });
});

/**
 * **An account with two profiles opens in the one used last** (ADR-0185 §3, ADR-0188 §2, #518) —
 * which the phone remembers, and which is checked against what the account holds *now*: an
 * administrator profile it no longer holds is Player (ADR-0188 §4), and Player is the default.
 */
describe('an account with two profiles', () => {
  const BOTH: EntryInput['profiles'] = { actsAsPlayer: true, administers: [OGRODY] };
  const IN_THE_APP = { named: true, hasPlayerProfile: true } as const;

  it('opens in the administrator profile it used last', () => {
    expect(
      entryDestination({
        ...IN_THE_APP,
        profiles: BOTH,
        lastProfile: { kind: 'administrator', clubId: OGRODY.clubId },
      }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('opens in Player when Player was used last', () => {
    expect(
      entryDestination({ ...IN_THE_APP, profiles: BOTH, lastProfile: { kind: 'player' } }),
    ).toEqual({ kind: 'app' });
  });

  it('opens in Player when the club it used last no longer has it', () => {
    expect(
      entryDestination({
        ...IN_THE_APP,
        profiles: BOTH,
        lastProfile: { kind: 'administrator', clubId: BONARKA.clubId },
      }),
    ).toEqual({ kind: 'app' });
  });

  // The profile was chosen, and choosing it is choosing not to be asked a player's questions now:
  // they are still owed, and switching back to Player is where they are asked.
  it('opens in the administrator profile ahead of anything the player side still owes', () => {
    expect(
      entryDestination({
        named: false,
        hasPlayerProfile: false,
        profiles: BOTH,
        lastProfile: { kind: 'administrator', clubId: OGRODY.clubId },
      }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('opens an account running two clubs in the one it used last', () => {
    expect(
      entryDestination({
        ...IN_THE_APP,
        profiles: { actsAsPlayer: false, administers: [BONARKA, OGRODY] },
        lastProfile: { kind: 'administrator', clubId: OGRODY.clubId },
      }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('opens an account that does not play on its first club, whatever Player said', () => {
    expect(
      entryDestination({
        ...IN_THE_APP,
        profiles: { actsAsPlayer: false, administers: [BONARKA, OGRODY] },
        lastProfile: { kind: 'player' },
      }),
    ).toEqual({ kind: 'administrator', clubId: BONARKA.clubId });
  });
});
