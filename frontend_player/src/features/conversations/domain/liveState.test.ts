/**
 * The three-way fold, and the two conditions that get dropped when it is written inside a
 * component: *only in the foreground*, and *only after a connect attempt has failed*.
 */

import { liveState } from './liveState';

describe('not live', () => {
  it('is drawn once a connect attempt has failed', () => {
    expect(liveState('lost', 'ordinary')).toBe('not-live');
  });

  /**
   * **Never on a cold open.** A room that is still opening its channel has nothing to report:
   * drawn here, every arrival on every room would flash the line.
   */
  it('is not drawn while the channel is still connecting', () => {
    expect(liveState('connecting', 'ordinary')).toBe('live');
  });

  it('is not drawn on an open channel', () => {
    expect(liveState('live', 'ordinary')).toBe('live');
  });

  /**
   * The stream is closed on the way to the background **deliberately**, which is not a failure —
   * so the line a returning player meets is the one their channel actually earns after it
   * re-opens, and never one about the seconds they were not looking.
   */
  it('is not drawn about a channel closed for the background', () => {
    expect(liveState('closed', 'ordinary')).toBe('live');
  });
});

describe('held', () => {
  /**
   * A hold and a dead channel can be true at once, and §3.6 asks for **one** note above the
   * composer. The fold answers with the one that changes what the player may do — and its
   * sentence already says reading works, which is the whole of what *not live* would have added.
   */
  it('wins over every stream standing, because it is the one that closes a control', () => {
    for (const stream of ['connecting', 'live', 'lost', 'closed'] as const) {
      expect(liveState(stream, 'held')).toBe('held');
    }
  });
});
