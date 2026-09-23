/**
 * **One challenge, the two answers, and the way out of every court that is still being arranged**
 * — the screen a row in the Chats inbox opens.
 *
 * A **state-keyed surface over the seven standings and two sides**, and never a `GameStanding`: a
 * challenge with no acceptance has no game to key a screen on, which is why there are two
 * state-keyed surfaces in this app and not one
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §2). Which
 * arm is drawn is `challengeArm`'s answer and never this file's — the sentence, the card block
 * and the controls are three readings of **one** fold, so the screen cannot say *They're waiting
 * on you* over a court it is also refusing to let you answer.
 *
 * **An ended court is drawn as one** ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §7): a `CALLED_OFF` court and a `DECLINED` one a departure deserted draw the row's sentence,
 * `EndedCourt` — every seat and what each person did — and **no arm**: no fill, no chat door, no
 * leave, no remove. Nothing on it is an act the server would accept. The two facts the sentence
 * and the court need that the detail read does not carry — `ended_by`, without which a presser's
 * seat reads *in* like the reader's, and `game_id` — are read off the row the list already holds
 * (`useChallengeRow`, merged by `asTheRowSays` before the fold), which is the row the tap came
 * in by and the read the tab bar keeps for its badge.
 *
 * **`ON` has an arm, and the inbox row is what reaches it.** The game's own standing owns the
 * **card** the moment a game exists (#324, ADR-0143 §8), so this arm draws the sentence and
 * nothing else — but a completed line-up keeps its row while it is news
 * ([`challengeInbox.ts`](../domain/challengeInbox.ts)), and every row is a door. **No system line
 * draws §13's `ON` sentences**: §3.4 refused the one #324 had given them, so the row and this arm
 * are the whole of it, and the row is what makes this one reachable. A stale route resolves here
 * too, which is now the second way in rather than the only one (§2.1, #390).
 *
 * ## The affordance is never removed without the space saying what took it
 *
 * §2.4's obligation, and it is discharged **by construction** rather than by a rule this file
 * remembers. The buttons and the standing sentence come out of the same fold, so there is no
 * state in which the controls are gone and the sentence has not changed: a refetch that lands
 * `LAPSED` draws *Your day ran out* in the same render that stops drawing `I'm in`, and a refusal
 * that re-reads does the same one round trip later. **The buttons are replaced by the sentence,
 * never by nothing.**
 *
 * **The offer may expire under the finger, and it is let to.** The read sits at `staleTime: 0`
 * with the app's own focus refetch, so a redraw can take **I'm in** away while the player is
 * looking at it. A mis-tap prevented beats a mis-tap refused.
 *
 * ## `I'm in` goes to the yes screen, and the door is drawn wherever the join answers
 *
 * Accepting is the one act in the app whose whole point is a room to talk in — the singles
 * room with the person who challenged you, the doubles room the people already in are already
 * talking in, its history included, because membership is derived and never cut at the moment
 * you joined. The reply is still the redraw, and then **the screen pushes the yes screen**
 * ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §1, [#433](https://github.com/Raketa02/Raketa/issues/433)): the faces, one word, two doors,
 * and the room is opened only by a tap on *Open the chat* there. This screen no longer walks
 * into the room by itself. The awaited door — the bounded rooms-list poll, and the rule that a
 * yes which completed the court waits for the row to carry its game — **moved into the yes
 * screen** and runs from the moment it opens; what stays here is the door on later visits, which
 * is ADR-0149 §3's join over the player's rooms read once (`useChatDoor`). It is drawn **on every
 * arm the join answers on**, not only the half-built court's: *no door rather than a dead one*
 * is the rule, and a room the list holds is a door on every arm whose reader is in it — an
 * accepted seat waiting on the others, a court that is on, the organiser once the first yes has
 * landed. Whether the reader is in it is the **fold's** answer (`readerIsInTheRoom`) and not the
 * list's alone: a decline or a withdraw invalidates the list rather than patching it, so for a
 * beat it can still hold a room the reader has just left, and the `answer` arm's reader has not
 * said yes to any.
 *
 * ## A half-built court is grown here, and nobody ends it for the others
 *
 * **Any live member may complete the line-up**
 * ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
 * §1): growing a court and ending one are different acts, and the commonest half-built court has
 * no organiser worth the name — a challenge born of two mutual yeses seats its pair on one side
 * and its "organiser" is only whoever said yes second. And since
 * [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §4 **a court somebody has joined is nobody's to end for the others**: *Withdraw* has left the
 * filling arm ([#428](https://github.com/Raketa02/Raketa/issues/428)), the organiser leaves it
 * like anybody else, and it ends by itself when nobody is on it, or one is with nobody deciding
 * (ADR-0175 §2). A court that has been a game has no end anybody presses at all
 * ([ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §1): it ends by its seats or by its hour.
 *
 * ## And it is not left here — leaving is the Chats row's swipe, only
 *
 * ***Leave the game*** stood on both live arms (ADR-0165 §1,
 * [#427](https://github.com/Raketa02/Raketa/issues/427)) and is gone (ADR-0175 §4): every court
 * a player has said yes to has a conversation row on Chats, and that row's swipe is the one
 * place a seat is given up, so a player who wants out goes where every seat is left from. The
 * fold's `mayLeave` went with it.
 *
 * ## Or removed here — by the organiser, while nobody has joined
 *
 * ***Remove the challenge*** on the arranging arm (ADR-0165 §4, #428), to the organiser exactly
 * while nobody besides them holds an accepted seat — before anybody has answered, and again once
 * everybody who joined has left, whatever seats are still deciding. It is the withdraw under the
 * name the record gives it now, and it is met as a **door** rather than as the control this
 * screen used to draw: `RemovalDoor`, the same one the organiser's Chats row reveals, which draws
 * the withdrawal's sheet in the removal's words and says a refusal on it. Whether it is drawn is
 * the fold's `mayRemove` — a court of one is removed, and a court with somebody is nobody's to
 * end, so the organiser leaves it from Chats like anybody else.
 *
 * **⚡ runs the fill and pushes the builder; the send is a separate press, on that screen, and it
 * pops back here** — which is why nothing in this flow calls `resetShellStack`. `landOnNow`'s
 * argument does not transfer: *"there is nothing left to be behind: the court is gone"* is false
 * here, where the thing behind is the challenge you were completing and is the surface that draws
 * the result.
 *
 * ## Offline is the shipped pattern exactly
 *
 * `BuilderScreen`'s: **the pair greys out, and one amber note sits above them** — not one per
 * button, which would say the same thing twice about one connection. The sentence is the shared
 * `does-not-resume` value unchanged, and **there is no third value**: the two split on
 * resumption, and a third keyed to the act would break the only distinction that function has.
 *
 * ## The forecast is drawn once, and the cards are drawn per person
 *
 * *The same figure rides on every card, because a forecast is a fact about the game rather than
 * about one person* — so it is the screen's line and not the card's, and a doubles court states
 * it once instead of three times. What is genuinely per pairing stays on the card: the Fit, the
 * distance, the reasons, the concern and what is at stake.
 *
 * ## An invitation a swipe produced says so, under the organiser's card
 *
 * *You said yes to Karol on Players* — one line, drawn exactly when the organiser is in the
 * reader's own outgoing list for this challenge's sport
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8). It is the reader's **own act** and nothing else: ADR-0143's refusal to tell an invitee
 * *why the engine picked them* is untouched, because Ania saying yes to Karol is a fact she
 * already holds. The list is Play's read (`useOutgoingInterest`, the deck's own query, through
 * Play's surface) and the rule is Play's (`saidYesTo`); nothing here waits for it — the card is
 * drawn without the line until the list lands and gains it without moving. Under the organiser's
 * card and no other seat's, so a doubles court with a card per person carries it once; the
 * organiser never reads it about themselves, because nobody is in their own outgoing list.
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';

import {
  PROVISIONAL_WORD,
  balanceReading,
  forecastAssumption,
  forecastHeading,
  saidYesTo,
  useFillChallengeSeats,
  useOutgoingInterest,
} from '@/features/play/types';
import { CONVERSATION_ROUTE, OPEN_THE_CHAT, useChatDoor } from '@/features/conversations/types';
import { sportLabel } from '@/features/onboarding/types';
import { ShellScreen } from '@/features/shell/types';
import { useCurrentUser } from '@/features/auth/types';
import { offlineMessage, recoveryMessage, type AppError } from '@/shared/errors';

import { useIsOnline } from '@/shared/lib/platform';
import { durationLeft } from '@/shared/formatting/durations';
import { playerName } from '@/shared/formatting/playerName';
import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';
import { Button, Note, theme } from '@/shared/ui';

import { actRefusal } from '../domain/actRefusal';
import { seatName } from '../domain/challenge';
import { fillRoute, yesRoute } from '../schemas/routeParams';
import {
  acceptedPlayers,
  asTheRowSays,
  challengeArm,
  readerIsInTheRoom,
  seatsAwaiting,
  type ChallengeDetail,
} from '../domain/challengeDetail';
import { useAnswerSeat, useChallenge } from '../hooks/useChallenge';
import { useChallengeRow } from '../hooks/useChallenges';
import type { SeatAnswerAct } from '../use-cases/answerSeat';

import { actOnRefusal } from './actOnRefusal';
import { ChallengeCard } from './ChallengeCard';
import { challengeErrorMessage } from './challengeErrorMessage';
import { EndedCourt } from './EndedCourt';
import {
  FILL_THE_SEATS,
  IM_IN,
  NOT_THIS_TIME,
  NO_CHALLENGE_HERE,
  pairingAbsenceLine,
  saidYesOnPlayersLine,
} from './challengeDetailPresentation';
import {
  CHALLENGE_SCREEN_TITLE,
  answerWindowLine,
  standingLine,
  yourAnswerWindowLine,
} from './challengePresentation';
import { RemovalDoor } from './RemovalDoor';

export interface ChallengeScreenProps {
  /** Validated by `schemas/routeParams.ts` before it reaches here; the route does that. */
  readonly challengeId: string;
}

export function ChallengeScreen({ challengeId }: ChallengeScreenProps) {
  const { data, isPending, error, refetch } = useChallenge(challengeId);
  const row = useChallengeRow(challengeId);
  const me = useCurrentUser().data?.id;

  if (data === undefined || me === undefined) {
    // **Who the reader is counts as still coming.** `useCurrentUser` is seeded by bootstrap and
    // answers first almost always, but *almost* is what the terminal sentence cannot afford:
    // drawn while it is in flight it says no challenge of yours has this address about a
    // challenge that is on screen a frame later.
    const arriving = isPending || (me === undefined && error === null);

    return (
      <ShellScreen title={CHALLENGE_SCREEN_TITLE} onBack={router.back}>
        {/* Three states with one sentence each, and none of them invents a fourth: the read is
            still coming, it failed, or no challenge of yours has this address — which is also
            what a sport this build cannot name resolves to. 10.1 forbids a spinner in this
            slot, so the first of the three draws nothing at all. */}
        {arriving ? null : error !== null ? (
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(error)}
          </Note>
        ) : (
          <Text style={s.line}>{NO_CHALLENGE_HERE}</Text>
        )}
      </ShellScreen>
    );
  }

  return (
    <Arrangement detail={asTheRowSays(data, row)} playerId={me} onReRead={() => void refetch()} />
  );
}

function Arrangement({
  detail,
  playerId,
  onReRead,
}: {
  readonly detail: ChallengeDetail;
  readonly playerId: string;
  readonly onReRead: () => void;
}) {
  const arm = challengeArm(detail, playerId);
  const answer = useAnswerSeat();
  const fill = useFillChallengeSeats();
  const online = useIsOnline();

  /**
   * **Where *Open the chat* goes**, or nothing — the client join ADR-0149 §3 settles, read here
   * because this is the surface that draws the door.
   *
   * It fails soft by construction: a challenge nobody has answered has no room, and a room is
   * destroyed when its episode ends, so the ordinary answer for both is **no door**. That is what
   * keeps `LINE_UP_INCOMPLETE`'s arm honest — this standing always has a room, because it is
   * reached by somebody accepting, and the absence is a list that has not landed yet rather than
   * a state anybody has to explain.
   *
   * Read once and never waited for: the room an accept opens is waited for on the yes screen
   * (ADR-0167 §1), and this door is the one drawn on every later visit.
   */
  const chat = useChatDoor(detail.challengeId);

  /**
   * **An invitation a swipe produced says so** (ADR-0169 §8): the reader's own outgoing yeses,
   * for the one line under the organiser's card. Read and never waited for — the card is drawn
   * without the line until the list lands, and gains it without moving.
   */
  const outgoing = useOutgoingInterest();
  const saidYesToOrganiser = saidYesTo(outgoing.data, detail.sport, detail.organiserId);

  /**
   * Which of the two is in flight, so the pressed control is the one that goes busy.
   *
   * Route-local and cleared by the reply, because it is a fact about a press rather than about
   * the challenge: leaving the screen throws it away, which is right for a tap nobody is
   * waiting on any more.
   */
  const [pressed, setPressed] = useState<SeatAnswerAct>();

  const cards = arm.kind === 'answer' || arm.kind === 'arranging' || arm.kind === 'filling';
  const sentence = arm.kind === 'unreadable' ? OUT_OF_DATE_GAP : standingLine(arm.facts);

  /**
   * **The whole of what a refused act on this screen costs it**, read once for the two acts whose
   * refusal is said *on the screen*.
   *
   * The two mutations refuse in the same three ways, so one reading is one sentence — and holding
   * a refusal per control would be two places for *say it* and *read it again* to be decided. The
   * two doors — the leave and the removal — say their refusals on their own sheets, and re-read
   * this detail through `actOn` once the sheet is dismissed.
   *
   * **The order is a precedence and the acts are not**, which is why {@link beginAnAct} clears
   * both before every press. A mutation's `error` **outlives its flight**: without the clear, an
   * answer refused ten minutes ago would still be first in this chain and would state its
   * sentence over a fill that has just failed for a different reason. Reading *the error of
   * whichever act was last pressed* by holding a third piece of state would be the same fact
   * written twice; resetting is the fact itself.
   */
  const failed: AppError | null = answer.error ?? fill.error;
  const refusal = failed === null ? undefined : actRefusal(failed);

  /**
   * **A refusal belongs to the press that caused it**, so a new press throws both away — and a
   * door opened does too, so a sheet never rises over a stale sentence.
   *
   * `BuilderScreen`'s own line before its send, arriving here because this screen grew from one
   * act to several: the sentence beneath the controls is read off whichever mutation still holds
   * an error, and a stale one is a screen explaining something the player is no longer doing.
   */
  function beginAnAct(): void {
    answer.reset();
    fill.reset();
  }

  /**
   * What a refusal costs, carried out — **a re-read, never a toast.**
   *
   * The standing the read comes back with **is** the sentence, and every sentence it can land
   * on is already written: *Your day ran out*, *You said no*, *You withdrew this*. `LEAVE` is
   * the one code for two cases, and there is nothing behind this screen to leave the player on.
   */
  function actOn(error: AppError): void {
    actOnRefusal(error, onReRead);
  }

  function send(act: SeatAnswerAct): void {
    beginAnAct();
    setPressed(act);
    answer.mutate(
      { challengeId: detail.challengeId, act },
      {
        onSettled: () => setPressed(undefined),
        // Only a yes lands somewhere: a no leaves the reader outside whatever room the others
        // keep, and the redraw's sentence is the whole of what it draws. A yes lands on the yes
        // screen the instant it is answered — whatever standing it came back with, even when
        // it completed the court — and the room is that screen's to wait for (ADR-0167 §1).
        // In the caller's own `onSuccess`, which runs after the hook's: the reply is in the
        // cache by the time the route changes, so the yes screen reads it as held.
        onSuccess: () => {
          if (act === 'accept') router.push(yesRoute(detail.challengeId, 'challenge'));
        },
        onError: actOn,
      },
    );
  }

  /**
   * **⚡ Fill the seats** — the act is `features/play`'s and the control is this screen's.
   *
   * It runs the fill and **pushes a builder holding a full court and a fresh search**, which is
   * *Find a game*'s own shape: press, the search runs, the builder arrives with a court on it.
   * That dissolves the *which search* question — the builder needs neither a stale `search_id`
   * nor a reconstructed line-up — and it makes *Pick players myself* work on the first screen
   * rather than after a mandatory ⚡.
   *
   * **Nothing outbound happens here.** Searching, browsing, seating, swapping and replacing
   * produce nothing outbound; the send is a separate press, on the builder, and it pops back to
   * this screen (ADR-0150 §7).
   *
   * The push is in the caller's own `onSuccess`, which runs after the hook's: the Play session
   * has begun and the line-up is seated by the time the route changes, so the builder never
   * renders a frame of an empty court it is about to fill.
   */
  function fillTheSeats(): void {
    beginAnAct();
    fill.mutate(
      {
        kind: 'challenge',
        sport: detail.sport,
        completing: {
          challengeId: detail.challengeId,
          accepted: acceptedPlayers(detail, playerId),
        },
      },
      {
        onSuccess: ({ record }) =>
          router.push({
            pathname: fillRoute(detail.challengeId),
            params: { search: record.searchId },
          }),
        onError: actOn,
      },
    );
  }

  // The court's own forecast, off whichever card carries one: it is the same figure on all of
  // them, so the first is the answer rather than a choice.
  const forecast = detail.seats.flatMap((seat) => seat.card?.pairing.forecast ?? [])[0];

  /**
   * The sentence a refused act writes, and **no new copy for the ones that re-read**: they are
   * handled by reading, and what they end up saying is the standing above. A connection that was
   * not there maps to the same `does-not-resume` sentence the amber note states, which is the one
   * value the two share by construction.
   */
  const said =
    refusal?.kind === 'SAY_SO' ? (
      <Note variant="coral" accessibilityRole="alert">
        {challengeErrorMessage(refusal.error)}
      </Note>
    ) : null;

  /**
   * One note above the controls rather than one per control, which would say the same thing
   * several times about one connection — `BuilderScreen`'s shipped pattern, and #327's.
   */
  const offline = online ? null : <Note variant="amber">{offlineMessage('does-not-resume')}</Note>;

  /**
   * ***Open the chat***, or nothing — the conversation's own door, drawn on every arm the join
   * answers on. The words are that feature's, so the surfaces that draw one cannot say different
   * things, and where it goes is a join over the player's rooms rather than a field on this
   * challenge (ADR-0149 §3). **No door rather than a dead one**: a room the list does not hold
   * draws nothing, which on a half-built court means only until the list has landed.
   *
   * **And only to a reader the room would hold** — `readerIsInTheRoom`, the fold's own answer.
   * The list is invalidated rather than patched by the reply that takes a reader out of a room,
   * so for a beat it still holds one they may no longer read; the join says a room exists, the
   * arm says whether this reader is in it, and a door is drawn only where both do.
   *
   * `secondary` everywhere, because opening a room you are already in is never the primary act
   * on a screen about a challenge — and on the arms with no other control it is still the only
   * one, so a `primary` there would be the one accent spent on a door.
   */
  const door =
    chat === undefined || !readerIsInTheRoom(arm) ? null : (
      <Button
        label={OPEN_THE_CHAT}
        variant="secondary"
        disabled={fill.isPending}
        onPress={() =>
          router.push({
            pathname: CONVERSATION_ROUTE,
            params: { conversationId: chat },
          })
        }
      />
    );

  /**
   * ***Remove the challenge***, or nothing — the removal's door, on the arranging arm to the
   * organiser nobody has joined (`mayRemove`). `secondary`: ending a court is never the primary
   * act on a screen about arranging one. The sheet, the act, its words and its refusals are
   * `RemovalDoor`'s — the same door the organiser's Chats row reveals — and the detail re-read
   * after a refusal is this screen's: *somebody's in now* re-folds the arm into one with no end
   * act on it. And on the reply it leaves: *You withdrew this* with nothing to press is a stop on
   * the way out of a thing the reader has just ended
   * ([#429](https://github.com/Raketa02/Raketa/issues/429)).
   */
  const remove =
    arm.kind === 'arranging' && arm.mayRemove ? (
      <RemovalDoor challengeId={detail.challengeId} onRefusal={actOn} onDone={router.back}>
        {(door) => (
          <View ref={door.control}>
            <Button
              label={door.label}
              variant="secondary"
              disabled={!online}
              onPress={() => {
                beginAnAct();
                door.open();
              }}
            />
          </View>
        )}
      </RemovalDoor>
    ) : null;

  /**
   * **Nothing is pinned on the ended court** (ADR-0172 §7) — no fill, no chat door, no leave, no
   * remove, whatever room the list may still hold for a beat — and an arm with no act of its own
   * and no door has nothing to pin either.
   */
  const nothingToPin = arm.kind === 'ended' || (door === null && remove === null);

  return (
    <ShellScreen
      title={CHALLENGE_SCREEN_TITLE}
      eyebrow={sportLabel(detail.sport)}
      onBack={router.back}
      action={
        arm.kind === 'filling' ? (
          /* **Grow · talk**, in that order, and everybody on the court sees the two
             ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
             §1, ADR-0165 §4). `LINE_UP_INCOMPLETE` *is not a waiting room*: the people who are in
             are in, so what this arm offers is finishing the court rather than waiting for it —
             and nobody ends it for the others. Leaving it is the Chats row's (ADR-0175 §4).

             ***Open the chat*** is the middle one, and it is the conversation's own door: the
             words are that feature's, so the three surfaces that draw one cannot say three
             different things, and where it goes is a join over the player's rooms rather than a
             field on this challenge (ADR-0149 §3). It is drawn only once that join answers —
             **no door rather than a dead one** — which on this standing means once the list has
             landed. It is `secondary` because there is one primary act on this screen and it is
             finishing the court; opening a room you are already in is not it. */
          <View style={s.answers}>
            {said}
            {offline}

            <Button
              label={FILL_THE_SEATS}
              size="lg"
              busy={fill.isPending}
              disabled={!online}
              onPress={fillTheSeats}
            />

            {door}
          </View>
        ) : arm.kind === 'answer' ? (
          <View style={s.answers}>
            {/* The deadline **stated, never counted down** — folded against the response's own
                `read_at` and never against this phone's clock. It gates nothing: the buttons
                beside it are drawn from the standing the platform sent. */}
            {arm.answerBy === undefined ? null : (
              <Text style={s.line}>
                {yourAnswerWindowLine(durationLeft(arm.answerBy, detail.readAt))}
              </Text>
            )}

            {said}
            {offline}

            <View style={s.pair}>
              <Button
                label={NOT_THIS_TIME}
                variant="secondary"
                style={s.answerControl}
                busy={pressed === 'decline'}
                disabled={!online || answer.isPending}
                onPress={() => send('decline')}
              />
              <Button
                label={IM_IN}
                style={s.answerControl}
                busy={pressed === 'accept'}
                disabled={!online || answer.isPending}
                onPress={() => send('accept')}
              />
            </View>
          </View>
        ) : nothingToPin ? undefined : (
          /* The arms with no act of their own — an accepted seat waiting on the others, a court
             that is on, the organiser waiting on answers — and a room the list holds. The door is
             what they offer, and only while it exists; the arranging arm offers the removal
             beside it, to the organiser nobody has joined. */
          <View style={s.answers}>
            {/* The greyed control this arm can hold is the removal, so the note that says why
                is drawn only where it is. */}
            {remove === null ? null : offline}
            {door}
            {remove}
          </View>
        )
      }
    >
      <Text style={s.standing}>{sentence}</Text>

      {/* The ended court: every seat and what each person did, under the sentence that says who
          ended it. Nothing else is drawn on this arm — no cards, no forecast, no controls. */}
      {arm.kind === 'ended' ? <EndedCourt court={arm.court} /> : null}

      {/* The organiser's own reading of the wait: §14's second sentence, once per seat, because
          the window is the seat's and a seat invited later starts its own day. */}
      {arm.kind === 'arranging' && arm.facts.side === 'organiser'
        ? seatsAwaiting(detail).map((seat, at) => (
            <Text key={`awaiting-${at}`} style={s.line}>
              {answerWindowLine({
                player: seat.player,
                duration: durationLeft(seat.answerBy, detail.readAt),
              })}
            </Text>
          ))
        : null}

      {/* The arrangement always answers, whatever the pairing could do — so the absence is a
          sentence in the cards' place and never a refusal to draw the screen. */}
      {cards && detail.pairingAbsence !== undefined ? (
        <Text style={s.line}>
          {pairingAbsenceLine(detail.pairingAbsence, sportLabel(detail.sport))}
        </Text>
      ) : null}

      {cards && forecast !== undefined ? (
        <View style={s.forecast}>
          <Text style={s.forecastHeading}>{forecastHeading(detail.seats.length)}</Text>
          {/* §B9's balance word beside the figure, because Part 13 forbids colour alone — and
              here there is no tint at all, so the word is the whole of it. `balanceReading` and
              not `balanceLabel`: the difference is one separator, and it is the difference
              between the two registers — a middot is a visual join, a comma is the pause a
              spoken clause needs. */}
          <Text style={s.line}>{balanceReading(forecast.pct)}</Text>

          {/* The word and its caveat are **two nodes and not one sentence**, which is
              `BuilderScreen`'s own shape: the caveat is the assumption's own line beneath the
              figure, and a join written here would be copy with no home in a deck. `null` covers
              *nothing was assumed* and *a code this build has no words for* alike, and the word
              above is what says there was one either way. */}
          {forecast.provisional ? <Text style={s.line}>{PROVISIONAL_WORD}</Text> : null}
          {forecast.provisional && forecast.assumption !== null ? (
            <Text style={s.line}>{forecastAssumption(forecast.assumption)}</Text>
          ) : null}
        </View>
      ) : null}

      {cards
        ? detail.seats.flatMap((seat, at) =>
            seat.card === undefined || seat.playerId === undefined
              ? []
              : [
                  <ChallengeCard
                    key={`seat-${at}`}
                    playerId={seat.playerId}
                    card={seat.card}
                    seats={detail.seats.length}
                  />,
                  /* Under the organiser's card and no other: the line is about the reader's
                     yes to the person who asked, and a doubles court draws a card per seat. */
                  ...(saidYesToOrganiser && seat.playerId === detail.organiserId
                    ? [
                        <Text key={`seat-${at}-said-yes`} style={s.line}>
                          {saidYesOnPlayersLine(playerName(seatName(seat)))}
                        </Text>,
                      ]
                    : []),
                ],
          )
        : null}
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  // The sibling state-keyed surface's own role: `GameScreen` draws its standing line at `h2`
  // over `ink`, and two screens whose whole job is stating a standing state it the same way.
  standing: { ...theme.type.h2, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  forecast: { gap: theme.space.xs },
  forecastHeading: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  answers: { gap: theme.space.sm },
  pair: { flexDirection: 'row', gap: theme.space.sm },
  answerControl: { flex: 1 },
});
