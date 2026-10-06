/**
 * This feature's query-key factory — the list, and one room under its own id.
 *
 * `GET /conversations` is a **query** and not a mutation: there is no id to mint one under and
 * asking again is asking the same question — *your rooms, right now*.
 *
 * **It takes the app-wide defaults whole**: nothing drawn from it is a number or a clock, and the
 * app's own focus refetch — already wired from `AppState` — is what makes it current when the
 * player opens the app. A conversation is append-ordered, so there is no ordering for a
 * background re-read to move under a finger.
 *
 * **And there is never a stream behind this list.** ADR-0147's *never build* list says so
 * outright: the live channel is one stream per **open** conversation, and a tab that opened one
 * per room would be a socket per room for a nudge nothing would redraw.
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
