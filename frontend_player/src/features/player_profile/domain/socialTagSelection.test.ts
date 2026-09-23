/**
 * The floor and the ceiling, with no renderer and no served response.
 *
 * These are the rules the picker obeys and the rules the profile editor will obey — the
 * same two screens against the same two numbers — which is why they are a function of a
 * selection and the served bounds rather than state inside a screen.
 *
 * **Every case states its bounds.** The platform serves 2 and 6 today and the picker reads
 * them; a suite that hardcoded them would pass against a client that ignored what it was
 * served, which is the one bug these rules exist to prevent.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import {
  sameSelection,
  selectionStanding,
  toggleSocialTag,
  type SocialTagSelectionBounds,
} from './socialTagSelection';

/** What the platform serves today: at least two, at most six. */
const SERVED: SocialTagSelectionBounds = { minimum: 2, maximum: 6 };

const SIX: readonly SocialTagId[] = [
  'STAYS_FOR_A_DRINK',
  'BOOKS_THE_NEXT_ONE',
  'PLAYS_TO_WIN',
  'QUIET_AND_FOCUSED',
  'HERE_TO_IMPROVE',
  'HERE_TO_COMPETE',
];

describe('adding a tag', () => {
  it('keeps the order the player pressed them in', () => {
    // Press order, not vocabulary order: what a player picked first is a fact about them,
    // and re-sorting the selection would throw it away before it ever reached the commit.
    expect(toggleSocialTag([], 'PLAYS_TO_WIN', SERVED)).toEqual({
      kind: 'selected',
      selection: ['PLAYS_TO_WIN'],
    });

    expect(toggleSocialTag(['PLAYS_TO_WIN'], 'STAYS_FOR_A_DRINK', SERVED)).toEqual({
      kind: 'selected',
      selection: ['PLAYS_TO_WIN', 'STAYS_FOR_A_DRINK'],
    });
  });

  it('leaves the selection it was given untouched', () => {
    const before: readonly SocialTagId[] = ['PLAYS_TO_WIN'];

    toggleSocialTag(before, 'HERE_TO_IMPROVE', SERVED);

    expect(before).toEqual(['PLAYS_TO_WIN']);
  });
});

describe('removing a tag', () => {
  it('drops it and leaves the rest in order', () => {
    expect(toggleSocialTag(SIX, 'PLAYS_TO_WIN', SERVED)).toEqual({
      kind: 'removed',
      selection: [
        'STAYS_FOR_A_DRINK',
        'BOOKS_THE_NEXT_ONE',
        'QUIET_AND_FOCUSED',
        'HERE_TO_IMPROVE',
        'HERE_TO_COMPETE',
      ],
    });
  });

  it('works at the ceiling, where adding does not', () => {
    // Story 21. The ceiling blocks adding and never blocks correcting — a player who has
    // filled it must still be able to change their mind about one of the six.
    expect(SIX).toHaveLength(SERVED.maximum);
    expect(toggleSocialTag(SIX, 'HERE_TO_COMPETE', SERVED).kind).toBe('removed');
  });
});

describe('the ceiling', () => {
  it('refuses the seventh and changes nothing', () => {
    // Story 20, and the reason it is a refusal rather than a rotation: dropping the oldest
    // to make room removes a choice the player made without telling them.
    const refused = toggleSocialTag(SIX, 'SHARES_A_LIFT', SERVED);

    expect(refused).toEqual({ kind: 'refused', reason: 'at-the-ceiling' });
    expect(refused).not.toHaveProperty('selection');
  });

  it('is the number that was served, not the number that was assumed', () => {
    const narrower: SocialTagSelectionBounds = { minimum: 1, maximum: 2 };

    expect(toggleSocialTag(['PLAYS_TO_WIN'], 'HERE_TO_IMPROVE', narrower).kind).toBe('selected');
    expect(
      toggleSocialTag(['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'], 'SHARES_A_LIFT', narrower).kind,
    ).toBe('refused');
  });
});

describe('the floor', () => {
  it('names how many more are needed, so a blocked control can say what is missing', () => {
    // Story 17: a disabled button is never a mystery. The count is the rule's answer, not
    // a sentence — the words are the presentation layer's and the number is this one's.
    expect(selectionStanding([], SERVED)).toEqual({ kind: 'short', missing: 2 });
    expect(selectionStanding(['PLAYS_TO_WIN'], SERVED)).toEqual({ kind: 'short', missing: 1 });
  });

  it('is met at the floor and stays met all the way to the ceiling', () => {
    expect(selectionStanding(['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'], SERVED)).toEqual({
      kind: 'ready',
    });
    expect(selectionStanding(SIX, SERVED)).toEqual({ kind: 'ready' });
  });

  it('is the number that was served, not the number that was assumed', () => {
    expect(selectionStanding(['PLAYS_TO_WIN'], { minimum: 3, maximum: 6 })).toEqual({
      kind: 'short',
      missing: 2,
    });
  });
});

/**
 * **Whether a draft is the selection the profile already holds** — what shuts *Save* on the
 * You tab (ADR-0179 §2). By membership and never by order: the profile holds the tags in the
 * vocabulary's order whatever order the picker pressed them in, so a draft that merely
 * re-ordered the same tags has nothing to save.
 */
describe('whether two selections are the same answer', () => {
  it('is by membership, whatever the order', () => {
    expect(
      sameSelection(['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'], ['HERE_TO_IMPROVE', 'PLAYS_TO_WIN']),
    ).toBe(true);
    expect(sameSelection(['PLAYS_TO_WIN'], ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'])).toBe(false);
    expect(
      sameSelection(['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'], ['PLAYS_TO_WIN', 'QUIET_AND_FOCUSED']),
    ).toBe(false);
    expect(sameSelection([], [])).toBe(true);
  });
});
