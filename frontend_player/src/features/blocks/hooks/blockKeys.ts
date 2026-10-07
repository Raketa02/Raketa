/**
 * **The blocks feature's query keys** — the one read, *Blocked players*, which the You tab's row
 * and the screen behind it both draw and every block and unblock re-reads; and the writes' own
 * keys, per person, so closing the confirm sheet can find a block still waiting for the network.
 */

export const blockKeys = {
  all: ['blocks'] as const,
  /** `GET /blocks` — the reader's own blocks, newest first. */
  list: () => [...blockKeys.all, 'list'] as const,
  /** A block of one person — the mutation's key, never a cache entry. */
  block: (playerId: string) => [...blockKeys.all, 'block', playerId] as const,
};
