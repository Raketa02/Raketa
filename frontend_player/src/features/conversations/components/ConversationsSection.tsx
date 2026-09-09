/**
 * **`CONVERSATIONS` on the Chats tab** — every room you are a member of, the ones that moved last
 * first.
 *
 * A section composed by the tab rather than a screen of its own, exactly as `ChallengesSection`
 * is above it and `GamesSection` is on Now: the tab owns its own sentences and nothing that is
 * drawn under it.
 *
 * **No count on the heading**, for the reason the section above it has none: the badge is the only
 * number on this screen and it counts unanswered challenges addressed to you, so a count of rooms
 * beside it would be two numbers meaning different things on one screen
 * ([#326](https://github.com/Raketa02/Raketa/issues/326) §6).
 *
 * **The order is the server's and is not re-derived here.** *By the last entry, newest first*, and
 * a room where nothing has happened yet orders on the moment it opened — an instant this list does
 * not carry, which is exactly why nothing on this side sorts.
 *
 * **Only live rooms are here, because there are only live rooms.** A conversation is destroyed
 * rather than delisted once its episode is over
 * ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)),
 * which is deliberately the opposite of the challenge list above — so there is no shelf life here
 * and nothing to apply one to. The difference is the difference between a record and a room.
 *
 * **A `LINE_UP_INCOMPLETE` challenge you accepted is drawn in both sections, and that is the
 * answer rather than a duplicate.** §13's own sentence asserts both facts in one breath —
 * *"You're in. {m} seats open, and the chat is already open"* — so the challenge row is the
 * **obligation** and this one is the **room**. Drawing it only under `CHALLENGES` would make it
 * the waiting room [#221](https://github.com/Raketa02/Raketa/issues/221) says it is not. It
 * happens by construction here: two contexts, two queries, and neither knows about the other.
 *
 * **This is the second copy of a section's shape, and it is recorded rather than extracted.**
 * `ChallengesSection` above it holds the same three conditional blocks, the same *has the list
 * landed and is the reader known* gate and the same three styles — and it is spelled again here
 * for the reason `conversationGeometry.ts` gives about the numbers: the only home a shared one
 * could have is the **shell**, whose `types.ts` re-exports `TabShell` and therefore mounts both
 * features, and a `StyleSheet.create` reached through that cycle resolves to `undefined` at module
 * scope. **A third section is the signal to find one** — `recoveryMessage.ts`'s own rule
 * ([#363](https://github.com/Raketa02/Raketa/issues/363)).
 *
 * **The empty line is the tab's rather than this feature's.** It says what lands on this *screen*,
 * and the screen is the shell's; what is this feature's is the heading, which names its own
 * content. Neither may assert that nothing is happening.
 */

import { StyleSheet, Text, View } from 'react-native';

import { recoveryMessage } from '@/shared/errors';
import { Note, theme } from '@/shared/ui';

import { useConversationRows } from '../hooks/useConversations';

import { ConversationRow } from './ConversationRow';
import { CONVERSATIONS_HEADING } from './conversationPresentation';

export interface ConversationsSectionProps {
  /**
   * What this section says when it holds nothing — one present-tense line naming the act, per
   * [10.1](../../../../docs/design-system.md#101-screen-structure).
   */
  readonly empty: string;
}

export function ConversationsSection({ empty }: ConversationsSectionProps) {
  const { data, error, playerId, rows } = useConversationRows();

  // *The list has landed and the reader is known.* Both, for `ChallengesSection`'s reason: gating
  // the empty line on the reader alone would draw *nobody has accepted yet* in the gap before the
  // list arrives, which is the flash 10.1's no-spinner rule is about from the other side.
  const answered = data !== undefined && playerId !== undefined;

  return (
    <View style={s.section}>
      <Text style={s.heading} accessibilityRole="header">
        {CONVERSATIONS_HEADING}
      </Text>

      {/* A read that failed is worth a sentence rather than an emptiness: a section that vanished
          on an error would be indistinguishable from having no rooms in it, and *nobody has
          accepted* is the one thing this section must not say wrongly. */}
      {error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(error)}
        </Note>
      ) : null}

      {/* A read still in flight draws **nothing at all**: 10.1 forbids a spinner in this slot. */}
      {error === null && answered && rows.length === 0 ? (
        <Text style={s.empty}>{empty}</Text>
      ) : null}

      {playerId === undefined
        ? null
        : rows.map((conversation) => (
            <ConversationRow
              key={conversation.conversationId}
              conversation={conversation}
              playerId={playerId}
            />
          ))}
    </View>
  );
}

const s = StyleSheet.create({
  section: { gap: theme.space.sm, marginTop: theme.space.lg },
  // 3.3 as amended: a section heading is `eyebrow` / `muted` / uppercase, and `h2` titles a card.
  heading: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  empty: { ...theme.type.tiny, color: theme.color.muted },
});
