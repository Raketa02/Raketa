/**
 * **The install referrer, read once** ([#756](https://github.com/Raketa02/Raketa/issues/756), the
 * friends mechanics §4.3) — on an Android phone's first launch, the link the public site's Google
 * Play button carried through the install is held as if it had been tapped. What it opens is walked
 * in `friendLink.test.tsx`; this is the *once*.
 */

import { readPhoneWideFlag } from '@/shared/lib/preferences';
import { fakeInstallReferrer } from '@/test-support/platform';

import { useHeldLinkStore } from '../store/heldLink.store';

import { readTheInstallReferrerOnce } from './installReferrerLink';

const held = () => useHeldLinkStore.getState().link;

afterEach(() => useHeldLinkStore.getState().reset());

describe('the install referrer', () => {
  it('holds a friend link it carried', async () => {
    const play = fakeInstallReferrer('https://rakieta.app/f/tk4m9q2z');

    await readTheInstallReferrerOnce(play);

    expect(held()).toEqual({ kind: 'friend', code: 'tk4m9q2z' });
  });

  it('holds a group link it carried', async () => {
    await readTheInstallReferrerOnce(fakeInstallReferrer('https://rakieta.app/join/k7pq2mxa'));

    expect(held()).toEqual({ kind: 'join', code: 'k7pq2mxa' });
  });

  it('is read on the first launch and never again', async () => {
    const play = fakeInstallReferrer('https://rakieta.app/f/tk4m9q2z');
    await readTheInstallReferrerOnce(play);
    useHeldLinkStore.getState().reset();

    await readTheInstallReferrerOnce(play);

    expect(play.reads).toBe(1);
    expect(held()).toBeNull();
    await expect(readPhoneWideFlag('installReferrerRead')).resolves.toBe(true);
  });

  /** An install from the store's own search carries Play's own words, which are no link. */
  it('holds nothing for a referrer that is no link, and is still read only once', async () => {
    const play = fakeInstallReferrer('utm_source=google-play&utm_medium=organic');

    await readTheInstallReferrerOnce(play);
    await readTheInstallReferrerOnce(play);

    expect(held()).toBeNull();
    expect(play.reads).toBe(1);
  });

  /** An iPhone has none, and neither has a phone whose Play did not answer. */
  it('holds nothing when there is no referrer', async () => {
    const play = fakeInstallReferrer(null);

    await readTheInstallReferrerOnce(play);

    expect(held()).toBeNull();
    expect(play.reads).toBe(1);
  });

  /** A link the phone opened while the first launch read Play is the newer, and is kept. */
  it('never replaces a link that arrived while it was being read', async () => {
    const play = fakeInstallReferrer('https://rakieta.app/f/tk4m9q2z');
    play.whileReading = () => useHeldLinkStore.getState().hold({ kind: 'join', code: 'k7pq2mxa' });

    await readTheInstallReferrerOnce(play);

    expect(held()).toEqual({ kind: 'join', code: 'k7pq2mxa' });
  });
});
