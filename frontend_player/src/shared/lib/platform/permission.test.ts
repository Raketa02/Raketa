/**
 * The four permission states, read off the two booleans and the status a native
 * permission response carries.
 *
 * This is the whole of the logic both ports contain, which is why it is a pure function
 * with its own test: everything else in `location.ts` and `imagePicking.ts` is a call to
 * a native module and a rename of its fields.
 *
 * The distinction that matters is the last one. **Denied and blocked are not the same
 * refusal** — a denied permission can be asked for again, at the moment the player
 * understands why, and a blocked one can only be changed in the OS settings app. A port
 * that collapsed them would either re-prompt forever against a system that answers
 * instantly and negatively, or send a player to Settings who had simply not been asked
 * yet.
 */

import { ensurePermission, permissionStateOf, type PermissionState } from './permission';

describe('reading a native permission response', () => {
  it('is granted when the platform granted it', () => {
    expect(permissionStateOf({ granted: true, canAskAgain: false, status: 'granted' })).toBe(
      'granted',
    );
  });

  it('is undetermined before the player has been asked at all', () => {
    expect(permissionStateOf({ granted: false, canAskAgain: true, status: 'undetermined' })).toBe(
      'undetermined',
    );
  });

  it('is denied when the player refused and may be asked again', () => {
    expect(permissionStateOf({ granted: false, canAskAgain: true, status: 'denied' })).toBe(
      'denied',
    );
  });

  it('is blocked when the player refused and the OS will not ask again', () => {
    expect(permissionStateOf({ granted: false, canAskAgain: false, status: 'denied' })).toBe(
      'blocked',
    );
  });

  /**
   * iOS reports `canAskAgain: false` alongside a granted permission — there is nothing
   * left to ask. Reading the booleans in the wrong order turns every granted permission
   * on that platform into a blocked one, which is a permission wall for players who said
   * yes.
   */
  it('reads granted before it reads whether it may ask again', () => {
    expect(permissionStateOf({ granted: true, canAskAgain: false, status: 'granted' })).not.toBe(
      'blocked',
    );
  });
});

/**
 * Asking, and the two states where asking is the wrong move.
 *
 * Both steps that reach a native capability had written this dance themselves, identically,
 * which is exactly how the two would have come to disagree about what a blocked permission
 * means. It belongs beside the vocabulary it is about.
 */
describe('asking for a permission', () => {
  /** A capability, as this rule sees one: something that can be asked, and asked again. */
  function capability(current: PermissionState, answer: PermissionState) {
    const asks: PermissionState[] = [];
    return {
      asks,
      getPermission: async () => current,
      requestPermission: async () => {
        asks.push(answer);
        return answer;
      },
    };
  }

  it('shows the prompt when the player has not been asked', async () => {
    const photos = capability('undetermined', 'granted');

    await expect(ensurePermission(photos)).resolves.toBe('granted');
    expect(photos.asks).toEqual(['granted']);
  });

  /** A refusal is not permanent: the OS will show the dialog again, so asking is the remedy. */
  it('shows it again after a refusal that may be re-asked', async () => {
    const photos = capability('denied', 'granted');

    await expect(ensurePermission(photos)).resolves.toBe('granted');
    expect(photos.asks).toEqual(['granted']);
  });

  it('does not prompt for something already granted', async () => {
    const photos = capability('granted', 'denied');

    await expect(ensurePermission(photos)).resolves.toBe('granted');
    expect(photos.asks).toEqual([]);
  });

  /**
   * The one that has to be right. A blocked permission is resolved by the OS instantly and
   * negatively without showing anything, so a caller that keeps asking loops forever against
   * a system that has already answered — and the player is never shown a thing.
   */
  it('never asks for one the OS has settled against', async () => {
    const photos = capability('blocked', 'granted');

    await expect(ensurePermission(photos)).resolves.toBe('blocked');
    expect(photos.asks).toEqual([]);
  });
});
