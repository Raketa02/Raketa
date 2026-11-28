/**
 * **A booked game's room** — the header, the stream and the composer
 * ([#556](https://github.com/Rakieta02/Rakieta/issues/556); the screens A4.4, the mechanics §14.3).
 *
 * *The place the people on a court talk about it*: opened with the booking and reached **only from
 * the game's details**, and **destroyed** once the game it names is over. That is why nothing here
 * has a shelf life to apply and why there is no *ended* state to draw — a room that is over is a
 * `404`, which is the same sentence as a room that was never yours
 * ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §5).
 *
 * It was the old loop's room too, with a plan card pinned under its header, quick chips asking
 * about the plan's empty slots and a *Details* door into the old game screen, until that loop was
 * removed ([#576](https://github.com/Rakieta02/Rakieta/issues/576)). A booked game has no plan to
 * fill — the booking is the plan — and *back* is the details it was opened from, by the stack.
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
 * there; the sentence a room owes about being out of touch is the *not live* line below.
 *
 * ## One line above the composer, and it is folded rather than checked
 *
 * The room stays current on its own — `useLiveConversation` follows it and a nudge invalidates the
 * read — and **says so honestly when it cannot**. What decides which of the three things it says
 * is `domain/liveState.ts` and not this file, because both of the conditions on *not live* are
 * ones a component drops quietly: it is drawn **only in the foreground** and **only after a
 * connect attempt has failed**, never on a cold open
 * ([ADR-0147](../../../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)
 * §8).
 *
 * **The composer is not disabled by it**, and that is the load-bearing half: a send is an ordinary
 * authenticated `POST` over a channel that is unidirectional by construction, so writing is
 * unaffected and closing the control would state something false about the half that works. The
 * fact has **two parts** — what you send still goes, and what they send arrives when this
 * reconnects — and only a sentence carries two.
 *
 * **Held is the other way round**: the account may read and may not write (ADR-0148 §9), so the
 * composer greys out behind **one** pre-emptive note. A greyed text field is acceptable **only**
 * because that note is above it and arrives first; absent the note it would be exactly the dead
 * end #324 refused.
 *
 * **A hold never removes the room**, and it never removes a control's explanation either: the
 * `account_held` refusal draws as the amber note rather than as a coral one, so the player is told
 * what their account is rather than told off for having tapped.
 *
 * ## The header's second line is the booking's word
 *
 * Handed in (`gameState`, the booking's word — *booked*, *needs result*), because the room knows its
 * game and not the booking's standing; the details that open it have just read that.
 *
 * ## The room owns its chrome: the top inset, and the bottom one because the bar stands down
 *
 * This screen does not go through `ShellScreen` — it is a header, an inverted list and a
 * composer over a keyboard, not a header over a scroller — and for a while it went
 * through nothing at all: a bare `KeyboardAvoidingView` at the root, with the header under the
 * status bar on Android and under the clock on iOS
 * ([#400](https://github.com/Rakieta02/Rakieta/issues/400)). The frame is now the same
 * `SafeAreaView` every other screen takes, and it takes **both edges**, which is the one place
 * in the app that is true of a screen inside the shell:
 *
 * - **The top edge** is what every screen takes, and it is `edges` rather than inset
 *   arithmetic, so a device this app has not seen is the library's problem and not this file's.
 * - **The bottom edge is the tab bar's everywhere else** — 10.1: *the tab bar owns the bottom
 *   safe-area inset and the CTA owns none*, because an inset applied twice is 34pt of nothing.
 *   Here the bar **stands down** (`shellTabs.barStandsDown`, read by `TabShell`): the composer
 *   replaces it so the keyboard and the stream get the whole screen, and with the bar gone the
 *   inset has no owner. Untaken, it is the field under the home indicator; so the room takes it,
 *   once, on its own frame — the exception 10.1's Part 16 row records.
 *
 * **The safe area is outside the keyboard avoidance, and the inset is on the frame rather than
 * in the composer's strip**, and both are the same fact about arithmetic. `KeyboardAvoidingView`
 * pads by however far the keyboard overlaps *its own* frame: with the safe area around it, that
 * frame ends at the home indicator's top and the composer lands on the keyboard exactly; with
 * the inset added inside the strip instead, the keyboard's full height is padded *and* the
 * inset stays, which is the 34pt gap above the keyboard that every chat app has shipped once.
 * The auth screens are the same shape — a safe area with both edges around a keyboard-avoiding
 * page — and this is the third screen with a keyboard and the first to have needed it under the
 * shell.
 */

import { useEffect, useMemo, useState } from 'react';
import { FlatList, KeyboardAvoidingView, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useCurrentUser } from '@/features/auth/types';
import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import { playerName } from '@/shared/formatting/playerName';
import { Note, theme } from '@/shared/ui';

import { liveState, writeStanding } from '../domain/liveState';
import { personNamed, type ConversationPerson } from '../domain/membership';
import { namesItsAuthors, type OpenConversation } from '../domain/room';
import { roomIsGone } from '../domain/roomGone';
import {
  mayPost,
  newClientMessageId,
  separatorAbove,
  streamOf,
  type StreamEntry,
} from '../domain/stream';
import { typists } from '../domain/typing';
import { conversationKeys } from '../hooks/conversationKeys';
import { useConversation, useSendMessage, useSendingMessages } from '../hooks/useConversation';
import { useLiveConversation } from '../hooks/useLiveConversation';
import { useTypingHeartbeat } from '../hooks/useTypingHeartbeat';

import { Bubble } from './Bubble';
import { Composer } from './Composer';
import { ConversationHeader } from './ConversationHeader';
import { conversationErrorMessage } from './conversationErrorMessage';
import {
  LIVE_NOTE,
  ROOM_OVER_LINE,
  systemLineSentence,
  typingLine,
} from './conversationPresentation';
import { DaySeparator } from './DaySeparator';
import { RoomAbsent } from './RoomAbsent';
import { SystemLine } from './SystemLine';
import { TypingBubble } from './TypingBubble';

export interface ConversationScreenProps {
  /** The room the booked game's join found — `useBookingRoom`, by the booking it is filed under. */
  readonly conversationId: string;
  /**
   * The header's second line after the sport — the booking's own word (*booked*), handed in by the
   * booked game's chat, which has just read the booking.
   */
  readonly gameState: string;
}

export function ConversationScreen({ conversationId, gameState }: ConversationScreenProps) {
  const { data, isPending, error, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useConversation(conversationId);
  const me = useCurrentUser().data?.id;

  /**
   * **A room that is gone before anything was read takes the screen with it**; one that goes
   * while it is on screen stays, as it was, and says so.
   *
   * The room can end while the reader is looking at it — the last other member leaves, and the
   * nudge that tells this phone is answered by `conversation_not_found` — so what discovers it is
   * a re-read rather than the read this screen mounted on. That used to leave the screen too, and
   * a player reading a room was on the list a moment later with the room gone from under them
   * ([#429](https://github.com/Rakieta02/Rakieta/issues/429)). What is held is still the
   * room as it last was, so it is drawn as it was, closed, with one sentence in the composer's
   * place (`ROOM_OVER_LINE`). Only a room nothing was ever read from has nothing to keep on screen,
   * and leaves — a stale row opened into a room that is not there. In an effect because it is a
   * **navigation**, and a router call made during a render is a side effect in the one place
   * React does not allow one.
   */
  const over = roomIsGone(error);
  useEffect(() => {
    if (over && data === undefined) router.back();
  }, [over, data]);

  if (data === undefined || me === undefined) {
    // **Who the reader is counts as still coming**: drawn while `useCurrentUser` is in flight,
    // the terminal sentence says no room of yours has this address about a room that is on
    // screen a frame later.
    return (
      <RoomAbsent arriving={isPending || (me === undefined && error === null)} error={error} />
    );
  }

  return (
    <Room
      opened={data}
      playerId={me}
      over={over}
      gameState={gameState}
      onPageBack={() => {
        if (hasNextPage && !isFetchingNextPage) void fetchNextPage();
      }}
    />
  );
}

function Room({
  opened,
  playerId,
  over,
  gameState,
  onPageBack,
}: {
  readonly opened: OpenConversation;
  readonly playerId: string;
  /** The room has ended since this was read. Drawn as it was, and nothing here writes. */
  readonly over: boolean;
  /** The header's word, the booking's (#556). */
  readonly gameState: string;
  readonly onPageBack: () => void;
}) {
  const { room, entries, people } = opened;

  const client = useQueryClient();
  const send = useSendMessage(room.conversationId);
  const sending = useSendingMessages(room.conversationId, playerId);

  /**
   * **What the room says about itself** — one fold, read once, over the channel and the account.
   *
   * The channel is followed for as long as this component is mounted, which is *one stream per
   * open conversation* by construction: there is nowhere else in the app that calls this, and the
   * Chats list one screen up deliberately has none. It is followed from **here** rather than from
   * the screen above, so the channel exists exactly while there is a room to keep current — a
   * nudge arriving during the first read would invalidate a query that is already in flight.
   */
  const { status: channel, typing } = useLiveConversation(room.conversationId);
  // The send is the one write on this screen, and so the one producer of *held*.
  const state = liveState(channel, writeStanding([send.error]));
  const held = state === 'held';

  /**
   * **Somebody is typing**, as a sentence — or nothing, which is how the bubble goes away.
   *
   * The roster is the channel's and already folded against it; what is done here is the reader
   * filter, which the server applies too and the ticket asks for twice, and the naming — off the
   * **members**, which makes this the one sentence on the screen that reads the roster rather than
   * `people`: a typist is gated on membership and is one (ADR-0156), where a system line's actor
   * need not be ([#409](https://github.com/Rakieta02/Rakieta/issues/409)). Not query cache state:
   * the frame is the fact.
   */
  const typingSentence = over ? undefined : typingLine(typists(typing, playerId), room.members);

  /**
   * The heartbeat, called from the composer's own keystrokes and from nowhere else — a keystroke
   * is the one event that means *the words are changing*, and the box being greyed under a hold
   * is the courtesy over `refused`, which is the mechanism.
   */
  const heartbeat = useTypingHeartbeat(room.conversationId, { refused: held || over });

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

  /**
   * The coral note's own refusal, and **a hold is not one of them.**
   *
   * `account_held` has a sentence already — the amber note below, which says what the account is
   * rather than what this tap did — so drawing both would say one fact twice and in two registers.
   * Every other code the send can be refused with is a thing about *this message*, and it keeps
   * the note beside the control that failed.
   */
  const sendRefusal = held || over ? null : send.error;

  function post(text: string): void {
    if (!mayPost(text)) return;

    send.reset();
    setDraft('');
    send.mutate(
      { conversationId: room.conversationId, text, clientMessageId: newClientMessageId() },
      {
        // The words go back in the box, because the retry is the control that failed and there
        // is nothing to retry with if the message is gone. A room that has gone is the one
        // refusal with nothing to retry at all: the read is asked again, and it is the read that
        // closes the room — one place decides that, and a send racing the nudge is not it.
        onError: (failed) => {
          if (roomIsGone(failed)) {
            void client.invalidateQueries({ queryKey: conversationKeys.room(room.conversationId) });
          } else setDraft(text);
        },
      },
    );
  }

  return (
    // Both edges, and the safe area outside the keyboard avoidance — the module note says why
    // each is the way round it is. The bottom edge is the one to notice: this is the screen the
    // bar stands down on, so the inset it owns everywhere else is the room's here.
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={s.page} behavior={KEYBOARD_AVOIDANCE}>
        <ConversationHeader
          room={room}
          playerId={playerId}
          gameState={gameState}
          onBack={router.back}
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
              people={people}
              playerId={playerId}
              showAuthors={showAuthors}
            />
          )}
          contentContainerStyle={s.stream}
          keyboardShouldPersistTaps="handled"
          // A room that has ended has nothing to page back into: the read would say so.
          onEndReached={over ? undefined : onPageBack}
          onEndReachedThreshold={0.4}
          // The header of an inverted list is its **newest** end, which is where a next bubble
          // would land — so the indicator takes that place and scrolls with the backlog, and is
          // never an entry: it has no `seq` and no key, and the list's data does not know it.
          ListHeaderComponent={
            typingSentence === undefined ? null : (
              <View style={s.typing}>
                <TypingBubble sentence={typingSentence} />
              </View>
            )
          }
        />

        {sendRefusal === null ? null : (
          <View style={s.refusal}>
            <Note variant="coral" accessibilityRole="alert">
              {conversationErrorMessage(sendRefusal)}
            </Note>
          </View>
        )}

        {/* Above the control it is about, because a greyed field is only acceptable where the
          sentence explaining it arrives first. `amber` on 1.3's reading: *watch this —
          reversible, not yet wrong*.

          **Only the hold is announced, and the split is what the player just did.** A hold arrives
          here as the answer to a send somebody pressed — no read serves it, so there is nothing to
          be pre-emptive with on the first tap — and a listener who got silence for their press
          would have the dead end this note exists to prevent. *Not live* is the opposite: it is a
          standing fact about the channel that goes true and false on its own roughly every quarter
          of an hour, and `alert` there would interrupt a player four times an hour to say nothing
          they need to act on. */}
        {state === 'live' || over ? null : (
          <View style={s.standing}>
            <Note variant="amber" accessibilityRole={held ? 'alert' : undefined}>
              {LIVE_NOTE[state]}
            </Note>
          </View>
        )}

        {/* The room has ended: the stream stays as it was, and where the composer stood one
            sentence says so — a fact, so neither amber nor coral, and announced, because it is
            the one thing that happened while the reader was looking and it happened to them. */}
        {over ? (
          <View style={s.standing}>
            <Note accessibilityRole="alert">{ROOM_OVER_LINE}</Note>
          </View>
        ) : (
          <Composer
            text={draft}
            onChange={(text) => {
              setDraft(text);
              heartbeat.beat();
            }}
            onPost={post}
            refused={held}
          />
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
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
  people,
  playerId,
  showAuthors,
}: {
  readonly entry: StreamEntry;
  readonly older: StreamEntry | undefined;
  /** Everybody the held pages name — what `{name}` and the author label are filled from. */
  readonly people: readonly ConversationPerson[];
  readonly playerId: string;
  readonly showAuthors: boolean;
}) {
  const day = separatorAbove(entry, older);

  return (
    <View style={s.row}>
      {day === undefined ? null : <DaySeparator day={day} />}

      {entry.kind === 'system-line' ? (
        <SystemLine sentence={systemLineSentence(entry, people)} />
      ) : (
        <Bubble
          text={entry.text}
          author={authorName(entry, people, playerId)}
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
 * room, read identically by everybody in it (`domain/membership.ts`). The handle is read off
 * `people`, as every `{name}` is — an author is always a member today, and one lookup for both
 * is what makes that a fact about the wire rather than a rule this screen keeps.
 */
function authorName(
  message: { readonly authorId: string },
  people: readonly ConversationPerson[],
  playerId: string,
): string {
  return message.authorId === playerId
    ? playerName({ kind: 'you' })
    : playerName(personNamed(people, message.authorId));
}

/**
 * What identifies a row.
 *
 * A system line is keyed by its `seq`, which is the whole of its identity within one room —
 * `(conversation_id, seq)`, and a room is what this list is.
 *
 * **A message is keyed by `client_message_id` whether or not it has landed**, and that is the
 * half worth stating: keyed by `seq` once the server answered, the row would be mounted under
 * one key while it was going out and another the moment it arrived, so the bubble a player is
 * looking at would be torn down and rebuilt at the instant nothing about it changed. One key
 * across the reconciliation is what makes *the bubble becomes the real one without moving* true
 * of the list as well as of the data.
 */
function keyOf(entry: StreamEntry): string {
  return entry.kind === 'system-line' ? `seq-${entry.seq}` : entry.clientMessageId;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  page: { flex: 1 },
  stream: { paddingHorizontal: theme.size.gutter, paddingVertical: theme.space.sm },
  row: { gap: theme.space.xs, paddingBottom: theme.space.xs },
  // The row's own step below it, so the bubble sits off the newest entry the way an entry would.
  typing: { paddingBottom: theme.space.xs },
  refusal: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.xs },
  standing: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.xs },
});
