/**
 * The `conversations` feature's only public surface.
 *
 * The room a challenge's first acceptance opens, and the tab that lists them. **This platform has
 * never had a messaging context**; the backend's arrived with
 * [#356](https://github.com/Raketa02/Raketa/issues/356) and this is the first client that reads
 * it ([#363](https://github.com/Raketa02/Raketa/issues/363)).
 *
 * **What is exported is what has a caller**, which today is the shell: the Chats tab composes the
 * section, and the route file mounts the landing a row is a door to. The read, the mapper, the
 * words and the two domain files stay internal — the section is the only thing that draws them,
 * and the stream that will draw them a second time
 * ([#364](https://github.com/Raketa02/Raketa/issues/364)) is this feature's own.
 */

/**
 * **The Chats tab's `CONVERSATIONS` section.**
 *
 * Composed by the shell under the tab's own words, exactly as `ChallengesSection` is above it: the
 * tab owns its citation and nothing that is drawn under it. It is handed the empty line because
 * that sentence is about the *screen* rather than about a conversation.
 */
export {
  ConversationsSection,
  type ConversationsSectionProps,
} from './components/ConversationsSection';

/**
 * **The screen a row opens** — mounted by `/chats/conversation/[conversationId]`.
 *
 * The header, the stream, the quick chips and the composer
 * ([#364](https://github.com/Raketa02/Raketa/issues/364)). The plan card pinned under its header
 * and the live channel behind it are [#366](https://github.com/Raketa02/Raketa/issues/366)'s and
 * [#365](https://github.com/Raketa02/Raketa/issues/365)'s, and the screen's own note says where
 * each goes.
 */
export { ConversationScreen, type ConversationScreenProps } from './components/ConversationScreen';

/**
 * **The game behind a room** — mounted by `/chats/conversation/[conversationId]/details`.
 *
 * `GameScreen` at a second route with the join in front of it, which is ADR-0149 §5's shape and
 * the reason the header's *Details* is a door rather than a drawn dead control.
 */
export {
  ConversationGameDetails,
  type ConversationGameDetailsProps,
} from './components/ConversationGameDetails';

/** Both routes' one param, validated before anything reads it. */
export { parseConversationRouteParams, type ConversationRouteParams } from './schemas/routeParams';

/**
 * **The chat door's words, wherever it is drawn** — *"the same words as every other chat door"*.
 *
 * Exported because three surfaces outside this feature will draw one and the sentence is about a
 * conversation: the challenge screen's half-built court is the first
 * ([#362](https://github.com/Raketa02/Raketa/issues/362)), and the game screen's planning arms and
 * Now's ✉ follow. One constant is what makes *the same words* true by construction.
 */
export { OPEN_THE_CHAT } from './components/conversationPresentation';

/**
 * **Whether the account may write, and the one sentence that says it may not** — exported for
 * the game screen's plan card ([#414](https://github.com/Raketa02/Raketa/issues/414)).
 *
 * A hold is a fact about the account and reaches this client only as `account_held` on a write;
 * `writeStanding` is the fold over every refusal a screen has met and `LIVE_NOTE.held` is the
 * amber note the room draws over its greyed controls. The plan card is drawn on the game screen
 * now as well as in the room, greys the same way off the same mutation cache, and owes the same
 * note — one fold and one constant is what makes *the same words* true by construction, exactly
 * as `OPEN_THE_CHAT` above.
 */
export { writeStanding } from './domain/liveState';
export { LIVE_NOTE } from './components/conversationPresentation';

/**
 * **Where that door goes**, spelled once for every surface that opens a room.
 *
 * Three features now push it — the challenge screen's half-built court, Now's card, and the row
 * itself — and each of the first two had begun by re-spelling the path at the call site. That is
 * the drift `GAME_ROUTE` was promoted out of a component to stop
 * ([#367](https://github.com/Raketa02/Raketa/issues/367)): *a second spelling of it at the call
 * site is how one of them goes stale.* Both segments under `/chats` carry a static kind above the
 * id, because a challenge id and a conversation id are different ids of different things.
 */
export { CONVERSATION_ROUTE } from './components/ConversationRow';

/**
 * **Where the chat door goes, from a challenge** — the client join ADR-0149 §3 settles.
 *
 * No route serves a challenge its conversation and ADR-0146 forbids one context holding the
 * other's ids, so the surface reads *the player's rooms* and finds the one this challenge opened.
 * **It fails soft**: no row is the ordinary state rather than an error, because a room opens on
 * the first acceptance and is destroyed when the episode ends.
 *
 * `useChatDoors` is the join over the whole list, for the rail — the door **and the faces** in the
 * room, because the rows carry every member's photograph and a game's seat carries none
 * ([#413](https://github.com/Raketa02/Raketa/issues/413)).
 *
 * `useAwaitedChatDoor` is the same join **waited for**: the room an acceptance opens is written
 * off the outbox after the accept has answered, so the screen that just said *I'm in* re-reads
 * the list on a short cadence until what it expects has landed, and stops at a bound
 * (`domain/roomOpening`). What it expects is the reply's to say — the room, or the room **and
 * its game** when the reply was `ON`, because a game is opened inline with that accept and the
 * room is told which a moment later.
 */
export {
  useAwaitedChatDoor,
  useChatDoor,
  useChatDoors,
  type RoomDoor,
  type RoomExpectation,
} from './hooks/useConversations';

/**
 * **The rooms' query key**, exported for the one thing outside this feature that can change the
 * list without being told about it in a reply.
 *
 * `features/challenges/` owns the two acts that do: an **accept** opens the first room or grows
 * one, and a **withdraw** destroys it outright — *destroyed, not delisted*
 * ([ADR-0142](../../../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md),
 * [ADR-0153](../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)).
 * Neither reply carries a conversation, so both **invalidate rather than patch**, and a client
 * that assembled or removed a row itself would be asserting something the server never described
 * to it.
 *
 * The key and nothing under it: the read, the mapper and the words stay this feature's, and what
 * crosses the seam is the address of a list rather than the shape of one.
 */
export { conversationKeys } from './hooks/conversationKeys';
