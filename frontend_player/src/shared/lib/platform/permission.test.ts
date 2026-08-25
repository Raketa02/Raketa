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

import { permissionStateOf } from './permission';

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
