/**
 * This feature's query-key factory — the list, and one room under its own id.
 *
 * `GET /conversations` is a **query** and not a mutation, for `challengeKeys`' own reason: there
 * is no id to mint one under and asking again is asking the same question — *your rooms, right
 * now*.
 *
 * **It takes the app-wide defaults whole**, which is the opposite of the challenge list beside it
 * and the difference is the badge. That list overrides `staleTime` to nought because a count sits
 * on permanent chrome and thirty seconds of staleness is a number saying something is waiting when
 * it is not; **nothing on this screen is a number, and no row here draws a clock**. What is left
 * is a list of rooms the player is reading, where the app's own focus refetch — already wired from
 * `AppState` — is what makes it current when they open the app.
 *
 * Play's two postures do not reach here either, and for the reason `the-loop-components.md` §2.4
 * states as a **scope clarification rather than an exception**: *nothing in Play
 * background-refetches* is written about a ranked list moving under a finger, and a conversation
 * is append-ordered.
 *
 * **And there is never a stream behind this list.** ADR-0147's *never build* list says so
 * outright: the live channel is one stream per **open** conversation, and a tab that opened one
 * per room would be a socket per row for a nudge nothing on this screen would redraw.
 */

export const conversationKeys = {
  all: ['conversations'] as const,
  /** Every room you are a member of. Not keyed by sport: one list, and rooms cross all four. */
  list: () => [...conversationKeys.all, 'list'] as const,
  /**
   * One room and every page of it a client is holding, under its own id.
   *
   * It is an **infinite** query's key: the entry the newest page opens on and everything paged
   * back from it live under one address, so a nudge invalidating this room re-reads what is held
   * rather than an arbitrary page of it.
   */
  room: (conversationId: string) => [...conversationKeys.all, 'room', conversationId] as const,
  /**
   * **The key every send in one room is made under** — a *mutation* key, and the only one in this
   * app.
   *
   * It is what `useMutationState` filters on to find the messages still going out, which is where
   * the optimistic bubbles come from: a paused send outlives the screen that made it, so the
   * mutation cache is the one place that list can honestly live. Keyed per room, because two rooms
   * open in one session must not draw each other's.
   */
  sending: (conversationId: string) =>
    [...conversationKeys.all, 'sending', conversationId] as const,
};
