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
 * composer, every quick chip and the plan's three slot chips all grey out behind **one**
 * pre-emptive note. One note for all of them, because it is one fact about the account and saying
 * it five times on one screen is the failure §1.6 names about counts. A greyed text field is
 * acceptable **only** because that note is above it and arrives first; absent the note it would be
 * exactly the dead end #324 refused.
 *
 * **A hold never removes the room**, and it never removes a control's explanation either: the
 * `account_held` refusal draws as the amber note rather than as a coral one, so the player is told
 * what their account is rather than told off for having tapped.
 *
 * ## The plan card is pinned under the header, and this feature imports the one that draws it
 *
 * Three slot chips from `features/plans` ([#366](https://github.com/Raketa02/Raketa/issues/366)),
 * pinned rather than emitted into the stream: every chat opens at its newest entry, so a card in
 * the scroll is a card you have to hunt for — and the plan is the thing the room exists to fill.
 *
 * **#364 anticipated a slot the route would fill and that shape was not taken**, which is recorded
 * here rather than left to be re-derived. Two facts about the room reach the card and neither is
 * knowable outside this component: which game the room completed into, which comes off the read
 * this screen mounts, and whether the account is **held**, which is the fold below. A slot filled
 * from the route would therefore have had to be a render prop taking a boolean, over a route that
 * had joined the room itself to find the game id — three props and a second join to avoid one
 * import through a feature's public surface, which this feature already makes to `features/games`
 * for the *Details* door.
 *
 * **The arrow that matters is a different one and is untouched.** ADR-0149 §1 fixes
 * `features/plans` → `features/games` and refuses the reverse; nothing anywhere refuses a room
 * composing the card that edits its own plan, and `plans` learns nothing about a conversation.
 *
 * The same read answers the quick chips: *one chip per unfilled slot, in slot order, plus `On my
 * way` when the agreed day is today*. A room whose line-up has not completed has **no game and no
 * plan**, which is `GET /plans`' own spelling for a game nothing has been agreed on — three
 * questions, no *On my way*, and no card at all.
 *
 * ## The room owns its chrome: the top inset, and the bottom one because the bar stands down
 *
 * This screen does not go through `ShellScreen` — it is a header, a pinned card, an inverted
 * list and a composer over a keyboard, not a header over a scroller — and for a while it went
 * through nothing at all: a bare `KeyboardAvoidingView` at the root, with the header under the
 * status bar on Android and under the clock on iOS
 * ([#400](https://github.com/Raketa02/Raketa/issues/400)). The frame is now the same
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
import { SafeAreaView } from 'react-native-safe-area-context';

import { useCurrentUser } from '@/features/auth/types';
import {
  cardStateWord,
  quickChips,
  RoomPlan,
  useGameCardName,
  usePlan,
  usePlanWriteRefusals,
} from '@/features/plans/types';
import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import { playerName } from '@/shared/formatting/playerName';
import { Note, theme } from '@/shared/ui';

import { liveState, writeStanding } from '../domain/liveState';
import { memberNamed, type ConversationMember } from '../domain/membership';
import { namesItsAuthors, type OpenConversation } from '../domain/room';
import { roomIsGone } from '../domain/roomGone';
import {
  mayPost,
  newClientMessageId,
  separatorAbove,
  streamOf,
  type StreamEntry,
} from '../domain/stream';
import { useConversation, useSendMessage, useSendingMessages } from '../hooks/useConversation';
import { useLiveConversation } from '../hooks/useLiveConversation';

import { Bubble } from './Bubble';
import { Composer } from './Composer';
import { ConversationHeader } from './ConversationHeader';
import { conversationErrorMessage } from './conversationErrorMessage';
import { LIVE_NOTE, systemLineSentence } from './conversationPresentation';
import { DaySeparator } from './DaySeparator';
import { RoomAbsent } from './RoomAbsent';
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

  /**
   * **A room that is gone takes the screen with it**, and this is the read that finds out.
   *
   * The room can be destroyed while the reader is looking at it — a withdraw does it in the same
   * act — so what discovers it is the app's own focus refetch rather than the read this screen
   * mounted on. In an effect because it is a **navigation**, and a router call made during a
   * render is a side effect in the one place React does not allow one.
   */
  useEffect(() => {
    if (roomIsGone(error)) router.back();
  }, [error]);

  if (data === undefined || me === undefined) {
    // **Who the reader is counts as still coming**, exactly as it does on the challenge screen:
    // drawn while `useCurrentUser` is in flight, the terminal sentence says no room of yours has
    // this address about a room that is on screen a frame later.
    return (
      <RoomAbsent arriving={isPending || (me === undefined && error === null)} error={error} />
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
   * What has been agreed — read here for the **quick chips**, which ask about the slots that are
   * still empty. The card below reads it again through its own join, and that is one query and
   * one cache: `GET /plans` is a list, and both readers are looking up the same row in it.
   */
  const { plan } = usePlan(room.gameId);

  /**
   * Where the game stands, for the header's second line — *the same state as the card in Now*
   * ([#401](https://github.com/Raketa02/Raketa/issues/401)). Folded by `features/plans` over the
   * two lists this screen already reads for the card and the chips, so it costs no request and
   * cannot disagree with the card three taps away. A room with no game has no name to fold and
   * the header draws the sport alone.
   */
  const card = useGameCardName(room.gameId);
  const gameState = card === undefined ? undefined : cardStateWord(card);

  /**
   * **What the room says about itself** — one fold, read once, over the channel and the account.
   *
   * The channel is followed for as long as this component is mounted, which is *one stream per
   * open conversation* by construction: there is nowhere else in the app that calls this, and the
   * Chats list one screen up deliberately has none. It is followed from **here** rather than from
   * the screen above, so the channel exists exactly while there is a room to keep current — a
   * nudge arriving during the first read would invalidate a query that is already in flight.
   */
  const channel = useLiveConversation(room.conversationId);
  // Every write on this screen is a producer of *held*, and four of the five are the plan card's.
  const planRefusals = usePlanWriteRefusals();
  const state = liveState(channel, writeStanding([send.error, ...planRefusals]));
  const held = state === 'held';

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
  const sendRefusal = held ? null : send.error;

  function post(text: string): void {
    if (!mayPost(text)) return;

    send.reset();
    setDraft('');
    send.mutate(
      { conversationId: room.conversationId, text, clientMessageId: newClientMessageId() },
      {
        // The words go back in the box, because the retry is the control that failed and there
        // is nothing to retry with if the message is gone. A room that has gone is the one
        // refusal with nothing to retry at all, and it takes the screen with it.
        onError: (failed) => {
          if (roomIsGone(failed)) router.back();
          else setDraft(text);
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
          {...(gameState === undefined ? {} : { gameState })}
          onBack={router.back}
          onOpenGame={() =>
            router.push({
              pathname: GAME_DETAILS_ROUTE,
              params: { conversationId: room.conversationId },
            })
          }
        />

        {/* Pinned under the header rather than emitted into the stream, which is the whole of
          §3.2's finding: the chat opens at its newest entry, so a card in the scroll is the first
          thing off-screen. A room with no game has no plan and draws none — the same nothing the
          header's absent *Details* draws, from the same field. */}
        {room.gameId === undefined ? null : <RoomPlan gameId={room.gameId} refused={held} />}

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

        {sendRefusal === null ? null : (
          <View style={s.refusal}>
            <Note variant="coral" accessibilityRole="alert">
              {conversationErrorMessage(sendRefusal)}
            </Note>
          </View>
        )}

        {/* Above every control it is about — the chips as well as the composer — because it is one
          fact about the screen rather than one per control, and because a greyed field is only
          acceptable where the sentence explaining it arrives first. `amber` on 1.3's reading:
          *watch this — reversible, not yet wrong*.

          **Only the hold is announced, and the split is what the player just did.** A hold arrives
          here as the answer to a send somebody pressed — no read serves it, so there is nothing to
          be pre-emptive with on the first tap — and a listener who got silence for their press
          would have the dead end this note exists to prevent. *Not live* is the opposite: it is a
          standing fact about the channel that goes true and false on its own roughly every quarter
          of an hour, and `alert` there would interrupt a player four times an hour to say nothing
          they need to act on. */}
        {state === 'live' ? null : (
          <View style={s.standing}>
            <Note variant="amber" accessibilityRole={held ? 'alert' : undefined}>
              {LIVE_NOTE[state]}
            </Note>
          </View>
        )}

        {/* One block — the chips, the field and Send — with one door out: Send and every chip
            post through the same `post`, so a chip send is an ordinary send (#402). */}
        <Composer
          text={draft}
          onChange={setDraft}
          chips={quickChips(plan, room.readAt)}
          onPost={post}
          refused={held}
        />
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
  const day = separatorAbove(entry, older);

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
  refusal: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.xs },
  standing: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.xs },
});
