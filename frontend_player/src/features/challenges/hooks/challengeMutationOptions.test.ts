/**
 * The one override every act in `challenges` makes on the app's mutation defaults.
 *
 * Asserted as a value rather than left to a screen, because the harm it prevents is invisible
 * at the site: an act that pauses succeeds later, looking exactly like one that worked.
 */

import { CHALLENGE_MUTATION_OPTIONS } from './challengeMutationOptions';

describe('an act in challenges with no connection', () => {
  it('fails now rather than deferring to the next reconnect', () => {
    // The answer window is derived **at the act**. A tap at 23:55 resumed at 00:10 would carry
    // a deadline the player did not choose — the tap and the request have to be one moment.
    expect(CHALLENGE_MUTATION_OPTIONS.networkMode).toBe('always');
  });

  it('is the whole mechanism, so a disabled button is left as the courtesy it is', () => {
    // Part 11: button disabling is UX, not correctness. The button alone would leave the
    // queue reachable.
    expect(Object.keys(CHALLENGE_MUTATION_OPTIONS)).toEqual(['networkMode']);
  });
});
