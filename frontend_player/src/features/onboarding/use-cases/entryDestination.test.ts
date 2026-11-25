/**
 * **The entry gate's rule over the account** (#874) — the same answer from the account as `/users/me`
 * serves it, whoever asks: the gate's hook, and the launch step that warms Home only for an account
 * headed for the tabs. The rule's own table is `entryDecision.test.ts`'s; these hold that the account
 * is read into it the one way.
 */

import type { AuthenticatedUser } from '@/features/auth/types';

import { decidedByTheLastProfile } from '../domain/entryDecision';

import { entryDestinationOf } from './entryDestination';

const OGRODY = { clubId: 'c0000000-0000-4000-8000-000000000001', clubName: 'Ogrody 33' };

/** Ada, as `/users/me` serves her: named, set up, a player who runs no club's groups. */
const ADA: AuthenticatedUser = {
  id: '11111111-2222-4333-8444-555555555555',
  email: 'ada@example.com',
  nickname: 'ada',
  hasPlayerProfile: true,
  profiles: { actsAsPlayer: true, administers: [], pendingInvitations: [], handovers: [] },
};

/** Ada, who also runs Ogrody 33's groups. */
const ADA_WHO_RUNS_A_CLUB: AuthenticatedUser = {
  ...ADA,
  profiles: { ...ADA.profiles, administers: [OGRODY] },
};

describe('the entry gate’s rule, over the account', () => {
  it('sends a named, set-up player into the app', () => {
    expect(entryDestinationOf(ADA)).toEqual({ kind: 'app' });
  });

  it('sends an account with no nickname to the naming step', () => {
    const { nickname: _, ...unnamed } = ADA;
    expect(entryDestinationOf(unnamed)).toEqual({ kind: 'naming' });
  });

  it('sends a named account with no Player profile to the profile steps', () => {
    expect(entryDestinationOf({ ...ADA, hasPlayerProfile: false })).toEqual({
      kind: 'social-steps',
    });
  });

  it('sends an account that only runs a club’s groups to its area', () => {
    expect(
      entryDestinationOf({
        ...ADA_WHO_RUNS_A_CLUB,
        profiles: { ...ADA_WHO_RUNS_A_CLUB.profiles, actsAsPlayer: false },
      }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('opens an account with both profiles in the one the phone says it wore last', () => {
    expect(
      entryDestinationOf(ADA_WHO_RUNS_A_CLUB, { kind: 'administrator', clubId: OGRODY.clubId }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
    expect(entryDestinationOf(ADA_WHO_RUNS_A_CLUB, { kind: 'player' })).toEqual({ kind: 'app' });
  });
});

describe('whose launch waits for the phone’s last profile', () => {
  it('is an account that runs a club’s groups, and nobody else', () => {
    expect(decidedByTheLastProfile(ADA_WHO_RUNS_A_CLUB.profiles)).toBe(true);
    expect(decidedByTheLastProfile(ADA.profiles)).toBe(false);
  });
});
