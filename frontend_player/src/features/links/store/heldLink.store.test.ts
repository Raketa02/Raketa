/** **The held link** — one at a time, the latest winning, let go of only by the link itself (#520). */

import { useHeldLinkStore } from './heldLink.store';

const held = () => useHeldLinkStore.getState().link;
const { hold, letGo, reset } = useHeldLinkStore.getState();

const FIRST = { kind: 'join', code: 'k7pq2mxa' } as const;
const SECOND = { kind: 'join', code: 'zzzzzzzz' } as const;

beforeEach(() => reset());

describe('the held link', () => {
  it('holds the link that arrived', () => {
    hold(FIRST);

    expect(held()).toEqual(FIRST);
  });

  /** A second link tapped before the first was answered is what the person wants now. */
  it('holds the latest in place of an earlier one', () => {
    hold(FIRST);
    hold(SECOND);

    expect(held()).toEqual(SECOND);
  });

  it('lets go of the link that was answered', () => {
    hold(FIRST);
    letGo({ kind: 'join', code: 'k7pq2mxa' });

    expect(held()).toBeNull();
  });

  /** An answer to the earlier link arriving late must not drop the newer one. */
  it('keeps a newer link when an older one is let go of', () => {
    hold(FIRST);
    hold(SECOND);
    letGo(FIRST);

    expect(held()).toEqual(SECOND);
  });
});
