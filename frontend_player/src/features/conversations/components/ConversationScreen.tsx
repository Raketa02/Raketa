/**
 * **The room** — the header, the stream, the quick chips and the composer.
 *
 * *The place two people who have agreed to play talk about it*
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3): opened by
 * the first acceptance, growing with each one, and **destroyed** once the episode it names is
 * over. That is why nothing here has a shelf life to apply and why there is no *ended* state to
 * draw — a room that is over is a `404`, which is the same sentence as a room that was never
 * yours ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §5).
 *
 * ## The stream opens at its newest entry and pages backward
 *
 * An **inverted** list, which is the whole of *opens at its newest*: the list is drawn from the
 * bottom, so the newest entry is where the eye starts with nothing scrolled and nothing measured.
 * Reaching its end — the visual top — asks for what is before the oldest thing held, and stops at
 * `seq` 1. **There is no `has_more` and nothing counts a gap**: a gapless sequence makes 1 the
 * beginning, and the gaplessness is the server's promise rather than something a reader checks.
 *
 * **Two components, never one with a branch** (ADR-0146, #338 §7). The stream picks between them
 * on the union's own discriminator, which is what a discriminated union is for — what is refused
 * is one component carrying a text field real for one arm and meaningless for the other.
 *
 * ## The send is optimistic, and it is the only optimistic act on this map
 *
 * `useConversation.ts` carries the argument. What the screen owns is the two halves a player sees:
 * the bubble appears at once, and **a refusal puts the words back in the box** with the sentence
 * beside it. Nothing is cleared until the send is made, so the retry is the control that failed —
 * *a retry belongs to the act*, one tab over.
 *
 * **A paused send draws nothing extra and that is deliberate.** It resumes on its own, so the
 * *does-not-resume* sentence would be false and the *resumes* one is written about a **read** —
 * *this will load as soon as you're back*. The honest signal is the bubble, which is already
 * there; the sentence a room owes about being out of touch is the *not live* line, and that is
 * [#365](https://github.com/Raketa02/Raketa/issues/365)'s, above this composer, with a stream
 * behind it that knows whether it failed to connect.
 *
 * ## What is not here yet, named rather than left to be noticed
 *
 * The **plan card** is pinned under this header and is
 * [#366](https://github.com/Raketa02/Raketa/issues/366)'s — three slot chips from
 * `features/plans`, rendered into this screen as a child, with neither feature importing the
 * other. Until it lands the room has no plan **and no surface on which a slot could be filled**,
 * so `quickChips` is asked about `undefined`, which is `GET /plans`' own spelling for a game
 * nothing has been agreed on: three questions and no *On my way*. The day that read exists the
 * screen hands one down and nothing else changes.
 *
 * The **live channel** is #365's, and until it lands what another member said arrives on the
 * app's own focus refetch.
 */

import { useMemo, useState } from 'react';
import { FlatList, KeyboardAvoidingView, Platform, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';

import { useCurrentUser } from '@/features/auth/types';
import { recoveryMessage } from '@/shared/errors';
import { playerName } from '@/shared/formatting/playerName';
import { Note, theme } from '@/shared/ui';

import { separatorBefore } from '../domain/entry';
import { memberNamed, type ConversationMember } from '../domain/membership';
import { quickChips } from '../domain/quickChips';
import { namesItsAuthors, type OpenConversation } from '../domain/room';
import { newClientMessageId, streamOf, type StreamEntry } from '../domain/stream';
import { useConversation, useSendMessage, useSendingMessages } from '../hooks/useConversation';

import { Bubble } from './Bubble';
import { Composer } from './Composer';
import { ConversationHeader } from './ConversationHeader';
import { conversationErrorMessage } from './conversationErrorMessage';
import {
  CONVERSATION_SCREEN_TITLE,
  NO_CONVERSATION_HERE,
  systemLineSentence,
} from './conversationPresentation';
import { DaySeparator } from './DaySeparator';
import { QuickChips } from './QuickChips';
import { SystemLine } from './SystemLine';

/**
 * The game behind this room, under the room's own address.
 *
 * Two routes over one screen component, which is ADR-0149 §9's shape: each lights its own column
 * and *back* is correct in both directions by construction, with no `from` parameter to make
 * `tabForPathname` impure. What is behind it grows three plan arms with
 * [#368](https://github.com/Raketa02/Raketa/issues/368); what this ticket owes it is a
 * destination, because a door that resolves to nothing is the dead control this map refuses.
 */
export const GAME_DETAILS_ROUTE = '/chats/conversation/[conversationId]/details';

export interface ConversationScreenProps {
  /** Validated by `schemas/routeParams.ts` before it reaches here; the route does that. */
  readonly conversationId: string;
}

export function ConversationScreen({ conversationId }: ConversationScreenProps) {
  const { data, isPending, error, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useConversation(conversationId);
  const me = useCurrentUser().data?.id;

  if (data === undefined || me === undefined) {
    // **Who the reader is counts as still coming**, exactly as it does on the challenge screen:
    // drawn while `useCurrentUser` is in flight, the terminal sentence says no room of yours has
    // this address about a room that is on screen a frame later.
    const arriving = isPending || (me === undefined && error === null);

    return (
      <View style={s.screen}>
        <ConversationChrome />
        {arriving ? null : error !== null ? (
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(error)}
          </Note>
        ) : (
          <Text style={s.line}>{NO_CONVERSATION_HERE}</Text>
        )}
      </View>
    );
  }

  return (
    <Room
      opened={data}
      playerId={me}
      onPageBack={() => {
        if (hasNextPage && !isFetchingNextPage) void fetchNextPage();
      }}
    />
  );
}

/** The header over the three states that have no room to name. See `CONVERSATION_SCREEN_TITLE`. */
function ConversationChrome() {
  return (
    <View style={s.chrome}>
      <Text accessibilityRole="header" style={s.chromeTitle}>
        {CONVERSATION_SCREEN_TITLE}
      </Text>
    </View>
  );
}

function Room({
  opened,
  playerId,
  onPageBack,
}: {
  readonly opened: OpenConversation;
  readonly playerId: string;
  readonly onPageBack: () => void;
}) {
  const { room, entries } = opened;

  const send = useSendMessage(room.conversationId);
  const sending = useSendingMessages(room.conversationId, playerId);

  /**
   * What is in the box.
   *
   * Route-local, because it is a fact about a press nobody has made yet: leaving the screen
   * throws away an unsent draft, which is the same answer every other unsent thing in this app
   * gets. It is cleared when the send is **made** and put back when the send is **refused**.
   */
  const [draft, setDraft] = useState('');

  /**
   * The stream, newest first — **which is what `inverted` wants and what opens it at the end.**
   *
   * `streamOf` puts what is still going out after what has landed and drops a send whose message
   * has arrived; reversing is the list's own requirement and not a second ordering.
   */
  const shown = useMemo(() => [...streamOf(entries, sending)].reverse(), [entries, sending]);

  const showAuthors = namesItsAuthors(room.members);
  const refused = send.error;

  function post(text: string): void {
    if (text.trim() === '') return;

    send.reset();
    setDraft('');
    send.mutate(
      { conversationId: room.conversationId, text, clientMessageId: newClientMessageId() },
      // The words go back in the box, because the retry is the control that failed and there is
      // nothing to retry with if the message is gone.
      { onError: () => setDraft(text) },
    );
  }

  return (
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ConversationHeader
        room={room}
        playerId={playerId}
        onBack={router.back}
        onOpenGame={() =>
          router.push({
            pathname: GAME_DETAILS_ROUTE,
            params: { conversationId: room.conversationId },
          })
        }
      />

      <FlatList
        // Named so a suite can scroll it: paging backward is a fact about what reaching the end
        // of this list asks for, and there is no other way to reach it from outside.
        testID="conversation-stream"
        inverted
        data={shown}
        keyExtractor={keyOf}
        renderItem={({ item, index }) => (
          <StreamRow
            entry={item}
            older={shown[index + 1]}
            members={room.members}
            playerId={playerId}
            showAuthors={showAuthors}
          />
        )}
        contentContainerStyle={s.stream}
        keyboardShouldPersistTaps="handled"
        onEndReached={onPageBack}
        onEndReachedThreshold={0.4}
      />

      {refused === null ? null : (
        <View style={s.refusal}>
          <Note variant="coral" accessibilityRole="alert">
            {conversationErrorMessage(refused)}
          </Note>
        </View>
      )}

      <QuickChips chips={quickChips(undefined, room.readAt)} onPost={post} />

      <Composer text={draft} onChange={setDraft} onSend={() => post(draft)} />
    </KeyboardAvoidingView>
  );
}

/**
 * One row of the stream: the separator that belongs above it, and the entry itself.
 *
 * The separator is drawn **inside** the row rather than through `ItemSeparatorComponent`, because
 * an inverted list draws its separators between cells in the list's own order and the day a
 * separator names is a fact about the entry **under** it. Rendering it here keeps the two
 * together whichever way the list is turned.
 */
function StreamRow({
  entry,
  older,
  members,
  playerId,
  showAuthors,
}: {
  readonly entry: StreamEntry;
  readonly older: StreamEntry | undefined;
  readonly members: readonly ConversationMember[];
  readonly playerId: string;
  readonly showAuthors: boolean;
}) {
  // A message still going out has no recorded moment, so it draws no separator and never
  // supplies one — `domain/stream.ts` on why nothing invents a *when*.
  const day =
    entry.kind === 'sending'
      ? undefined
      : separatorBefore(entry, older === undefined || older.kind === 'sending' ? undefined : older);

  return (
    <View style={s.row}>
      {day === undefined ? null : <DaySeparator day={day} />}

      {entry.kind === 'system-line' ? (
        <SystemLine sentence={systemLineSentence(entry, members, 'full')} />
      ) : (
        <Bubble
          text={entry.text}
          author={authorName(entry, members, playerId)}
          mine={entry.authorId === playerId}
          showAuthor={showAuthors && entry.authorId !== playerId}
        />
      )}
    </View>
  );
}

/**
 * Who said it — **`You` on the reader's own, and the whole handle on everybody else's.**
 *
 * `playerName`'s `you` arm is right here and wrong on a system line: a bubble is read *by* the
 * person it is addressed to, where a system line is a third-person record of what happened in a
 * room, read identically by everybody in it (`domain/membership.ts`).
 */
function authorName(
  message: { readonly authorId: string },
  members: readonly ConversationMember[],
  playerId: string,
): string {
  return message.authorId === playerId
    ? playerName({ kind: 'you' })
    : playerName(memberNamed(members, message.authorId));
}

/**
 * What identifies a row.
 *
 * `(conversation_id, seq)` identifies a recorded entry and a message has no id of its own, so
 * within one room the `seq` is it. A send that has not landed has no `seq` at all and is keyed by
 * the id it will be reconciled on — which is also what keeps the list from remounting the row
 * when the real message replaces it under a different key.
 */
function keyOf(entry: StreamEntry): string {
  return entry.kind === 'sending' ? entry.clientMessageId : `seq-${entry.seq}`;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  chrome: { paddingHorizontal: theme.size.gutter, paddingVertical: theme.space.md },
  chromeTitle: { ...theme.type.h1, color: theme.color.ink },
  stream: { paddingHorizontal: theme.size.gutter, paddingVertical: theme.space.sm },
  row: { gap: theme.space.xs, paddingBottom: theme.space.xs },
  refusal: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.xs },
  line: { ...theme.type.tiny, color: theme.color.muted, paddingHorizontal: theme.size.gutter },
});
