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
 * A landing today, and [#364](https://github.com/Raketa02/Raketa/issues/364)'s screen tomorrow.
 * See its own note for why it arrives with the row rather than after it.
 */
export { ConversationScreen } from './components/ConversationScreen';
