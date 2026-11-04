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
  readPhoneFlag,
  readPhonePreference,
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
