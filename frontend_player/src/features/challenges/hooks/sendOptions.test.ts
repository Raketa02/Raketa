/**
 * The one override the send makes on the app's mutation defaults.
 *
 * Asserted as a value rather than left to a screen, because the harm it prevents is invisible
 * at the site: a send that pauses succeeds later, looking exactly like a send that worked.
 */

import { SEND_MUTATION_OPTIONS } from './sendOptions';

describe('sending a challenge with no connection', () => {
  it('fails now rather than deferring to the next reconnect', () => {
    // The answer window is derived **at send**. A tap at 23:55 resumed at 00:10 would carry a
    // deadline the player did not choose — the tap and the send have to be one moment.
    expect(SEND_MUTATION_OPTIONS.networkMode).toBe('always');
  });

  it('is the whole mechanism, so a disabled button is left as the courtesy it is', () => {
    // Part 11: button disabling is UX, not correctness. The button alone would leave the
    // queue reachable.
    expect(Object.keys(SEND_MUTATION_OPTIONS)).toEqual(['networkMode']);
  });
});
