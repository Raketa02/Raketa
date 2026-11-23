/**
 * **The phone-preferences store, at its own seam** — what one account saved is read back by that
 * account, by nobody else, and by nobody at all once the session ends
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §2, §3).
 *
 * The device's storage is jest's in-memory AsyncStorage, emptied after every test by
 * `jest.setup.js`. The sign-out is the real `endSession`, because *wiped at sign-out* is a step
 * of that sequence rather than something a screen remembers to do.
 */

import { endSession } from '@/shared/lib/auth';

import {
  raisePhoneFlag,
  raisePhoneWideFlag,
  readPhoneFlag,
  readPhonePreference,
  readPhoneWideFlag,
  savePhonePreference,
} from './phonePreferences';

const ADA = '11111111-2222-4333-8444-555555555555';
const BORIS = '99999999-8888-4777-8666-555555555555';

describe('the phone-preferences store', () => {
  it('reads back what an account saved', async () => {
    await savePhonePreference(ADA, 'playSegment', 'explore');

    await expect(readPhonePreference(ADA, 'playSegment')).resolves.toBe('explore');
  });

  it('has nothing for an account that saved nothing', async () => {
    await expect(readPhonePreference(ADA, 'playSegment')).resolves.toBeUndefined();
  });

  it('keeps one account’s choice from the next account on the same phone', async () => {
    await savePhonePreference(ADA, 'playSegment', 'explore');

    await expect(readPhonePreference(BORIS, 'playSegment')).resolves.toBeUndefined();
  });

  it('replaces a value rather than keeping the first', async () => {
    await savePhonePreference(ADA, 'playSegment', 'explore');
    await savePhonePreference(ADA, 'playSegment', 'groups');

    await expect(readPhonePreference(ADA, 'playSegment')).resolves.toBe('groups');
  });

  it('keeps each value apart from the others', async () => {
    await savePhonePreference(ADA, 'playSegment', 'explore');
    await savePhonePreference(ADA, 'lastSport', 'tennis');

    await expect(readPhonePreference(ADA, 'playSegment')).resolves.toBe('explore');
    await expect(readPhonePreference(ADA, 'lastSport')).resolves.toBe('tennis');
  });

  it('forgets every account’s choices when a session ends', async () => {
    await savePhonePreference(ADA, 'playSegment', 'explore');
    await savePhonePreference(ADA, 'lastSport', 'tennis');
    await savePhonePreference(BORIS, 'playSegment', 'explore');

    await endSession('requested');

    await expect(readPhonePreference(ADA, 'playSegment')).resolves.toBeUndefined();
    await expect(readPhonePreference(ADA, 'lastSport')).resolves.toBeUndefined();
    await expect(readPhonePreference(BORIS, 'playSegment')).resolves.toBeUndefined();
  });
});

/**
 * **The rows seen on a group page's tabs** ([ADR-0208](../../../../../docs/adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md)):
 * one entry per group, sport and tab, per account like every value, and forgotten at sign-out with
 * the rest.
 */
describe('the rows seen on a group page’s tabs', () => {
  const FILL_IN = 'seenRows.a0000000-0000-4000-8000-000000000005.padel.fillIn';
  const YOURE_IN = 'seenRows.a0000000-0000-4000-8000-000000000005.padel.youreIn';

  it('keeps each tab’s entry apart, and each account’s', async () => {
    await savePhonePreference(ADA, FILL_IN, '["b1"]');
    await savePhonePreference(ADA, YOURE_IN, '["p1"]');

    await expect(readPhonePreference(ADA, FILL_IN)).resolves.toBe('["b1"]');
    await expect(readPhonePreference(ADA, YOURE_IN)).resolves.toBe('["p1"]');
    await expect(readPhonePreference(BORIS, FILL_IN)).resolves.toBeUndefined();
  });

  it('forgets them when a session ends', async () => {
    await savePhonePreference(ADA, FILL_IN, '["b1"]');

    await endSession('session-invalidated');

    await expect(readPhonePreference(ADA, FILL_IN)).resolves.toBeUndefined();
  });
});

/**
 * **The one value kept past a session** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §8, as amended 2026-11-04): *the guide on Your rating was shown* is kept per account on this
 * phone, and outlives the session — the same account signing in again never sees the guide, and a
 * second account on the phone does, once.
 */
describe('a flag the phone keeps for an account', () => {
  it('is down until it is raised', async () => {
    await expect(readPhoneFlag(ADA, 'ratingGuideShown')).resolves.toBe(false);
  });

  it('stays up once raised', async () => {
    await raisePhoneFlag(ADA, 'ratingGuideShown');

    await expect(readPhoneFlag(ADA, 'ratingGuideShown')).resolves.toBe(true);
  });

  it('is the account’s own: another account on the phone finds it down', async () => {
    await raisePhoneFlag(ADA, 'ratingGuideShown');

    await expect(readPhoneFlag(BORIS, 'ratingGuideShown')).resolves.toBe(false);
  });

  it('is kept when a session ends, while every account’s choices go', async () => {
    await raisePhoneFlag(ADA, 'ratingGuideShown');
    await savePhonePreference(ADA, 'playSegment', 'explore');

    await endSession('requested');

    await expect(readPhoneFlag(ADA, 'ratingGuideShown')).resolves.toBe(true);
    await expect(readPhonePreference(ADA, 'playSegment')).resolves.toBeUndefined();
  });
});

/**
 * **A flag the phone keeps for nobody in particular** (#756) — *the install referrer was read*,
 * raised on the app's first launch, before anybody has signed in, and never lowered: not by a
 * sign-out, and not by another account signing in.
 */
describe('a flag the phone keeps for itself', () => {
  it('is down until it is raised, and stays up once it is', async () => {
    await expect(readPhoneWideFlag('installReferrerRead')).resolves.toBe(false);

    await raisePhoneWideFlag('installReferrerRead');

    await expect(readPhoneWideFlag('installReferrerRead')).resolves.toBe(true);
  });

  it('is kept when a session ends', async () => {
    await raisePhoneWideFlag('installReferrerRead');

    await endSession('requested');

    await expect(readPhoneWideFlag('installReferrerRead')).resolves.toBe(true);
  });

  it('is not an account’s flag of the same name', async () => {
    await raisePhoneWideFlag('installReferrerRead');

    await expect(readPhoneFlag(ADA, 'ratingGuideShown')).resolves.toBe(false);
  });
});
