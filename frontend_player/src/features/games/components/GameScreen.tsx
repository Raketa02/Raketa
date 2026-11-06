/**
 * **The result argument, on a screen of its own.**
 *
 * `prototype/result-confirmation` offered three homes for it — inside the Now state card, a
 * sheet over Now, or a route — and the first two were arguments about a card this build does not
 * have and this ticket is not building. What is left is **variant C**, and its own stated cost
 * falls away with them: *"a player is taken off Now to answer a card that was already on Now"* is
 * a cost against a card, and Now carries a **list** here. What the route buys is what the
 * prototype said only it could buy — room to name both sides of every score, room to show a
 * counter and the score it answers **side by side**, and room for the consequence as a sentence
 * rather than a fact line, which is the whole of *when silence makes a score the result is said
 * before it happens* (#656).
 *
 * **The layout is that variant's, and so is most of the copy**: the clock block, the *still on
 * the table* / *yours* pair over the counter's grid, the two-button footer, and the fact list a
 * game with no score ends on. What is rewritten is only what the model moved. Names came back
 * with the handle on a seat, under `gamePresentation`'s rule: a person where a person acted, a
 * side where a side did.
 *
 * ## One screen, every state, and the state is derived
 *
 * `domain/resultArgument.ts` decides which; nothing here reads a standing directly. That matters
 * most at the two states that look alike and are not: **a correction and a counter are the same
 * request** and completely different news, so the screen that offers one never offers the other,
 * and the words for each say which it is before the tap.
 *
 * ## A disagreement draws both scores, and the control names the one it agrees with
 *
 * Two scores on the table used to cross with **neither** of them on the response, so the screen
 * stated the ending and offered nothing — *"the client could offer the act only by asking
 * somebody to agree with a score it cannot show them"*. Both travel now
 * ([#317](https://github.com/Raketa02/Raketa/issues/317)), so the reader's own is drawn quiet
 * above the other side's and the agreement is offered under them, named for the score it agrees
 * with. There is no counter there: that side has had its one turn.
 *
 * ## The grid opens over what is already on screen, and closes on the answer
 *
 * On a game nobody has claimed, there is nothing to open over — the grid *is* the screen. On a
 * standing score it opens **pre-loaded with the score it answers**, because a real disagreement
 * is usually one digit, and an unchanged one is refused here rather than paid for a day later:
 * two matching scores nobody accepts still leave the game unscored.
 *
 * ## The card asking how they were is the last thing on it
 *
 * `features/sportsmanship/`'s, composed here and drawn under everything above — the moment a
 * player has to think about how an evening went is the moment they are looking at what came of
 * it. It used to sit above the games list on Now
 * ([#386](https://github.com/Raketa02/Raketa/issues/386)); moving it here costs the one thing
 * that surfaced it, so a player who never re-opens a settled game never sees a card. That is a
 * fair trade only because ignoring one costs nothing and always did.
 *
 * **It draws itself or nothing, and this screen decides neither.** Whether a card is open is the
 * server's answer — settled, a day old, inside its week — so what is composed here is the court
 * and never a condition. It happens to be drawable only in the two states `actsOffered` leaves
 * empty, which is why its own send is never a second control beside a pinned one.
 *
 * ## The refusal is a sentence, never a closed control
 *
 * A grid validated on every keystroke says *a set cannot end level* while somebody is typing the
 * second 6 of 6-4. So the check runs **on the press**, and what a bad draft gets is a sentence
 * under the grid — the same posture sign-up's attestation takes, and the same one the profile
 * commit takes when the server refuses a rule a picker already enforced.
 *
 * ## Both writes pause offline, and neither is optimistic
 *
 * A standing is folded from the record and the clock, so the only client that can be right about
 * what a game becomes is one that asks. And neither act carries a deadline the player chose — a
 * proposal's day starts whenever it lands, and an agreement settles whenever it lands (#654) — so
 * both take the app's queue, and the sentence beside a paused control says it will resume.
 *
 * ## For fun asks nothing, and a score may still go in
 *
 * A friendly reads *Played* before its score and after it ([#656](https://github.com/Raketa02/Raketa/issues/656)):
 * nobody is asked to agree, so there is no *Is that right?*, no clock and nothing pinned once a
 * score is up. Until one is, the grid is the screen under that heading, as on the entry, because
 * the one way here is a door named *Add the score*.
 *
 * ## The plan arms are a slot, and this screen knows nothing about what fills it
 *
 * `ResultScreen` became `GameScreen` because one screen shows a game **whatever state it is in**
 * ([#368](https://github.com/Raketa02/Raketa/issues/368),
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §5): the plan
 * while it is being agreed, the score once it has been played. **Grown, not replaced** — a hand-off
 * in the middle of one standing's life would give a player two different screens for the same game
 * depending which day they tapped it.
 *
 * What grew is one `ReactNode`, rendered on the `awaiting-entry` arm and nowhere else.
 * [ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §2: *`games` owns the frame, the court and the result arms, and `plans` renders the three slots
 * into it. **Neither type crosses.*** So there is no `Plan` here, no ladder, no rung and no import
 * — `eslint.config.mjs` refuses one — and **the three arms §5.1 names are three readings of that
 * one slot**, because §22.6 settles that *the rungs differ by the clock and not by the
 * arrangement*.
 *
 * **One route mounts this component now** — a booked game's result, `/booking/[id]/result`,
 * on the score lead with the four slots empty ([#576](https://github.com/Raketa02/Raketa/issues/576)).
 * It was mounted at `/games/[gameId]` and behind a room's *Details* too, filled by the old loop's
 * plan, until that loop was removed; the plan lead and the slots below are that loop's, kept until
 * a ticket of its own folds the screen to the one lead it has.
 *
 * ## Three plan arms, and the one word that tells them apart
 *
 * §5.2 lands two different cards on two different things inside one standing: *Planning* and *Game
 * on* arrive at **the plan**, *Needs result* at **the score grid**. The ladder that tells them
 * apart reads a plan, so the fold is `features/plans`' and what arrives here is
 * `EntryLead` — a word in this feature's own vocabulary rather than a rung in somebody else's.
 *
 * **It changes what leads and never what is offered.** *We played* is available on **every** entry
 * arm, because `standing_of` gates entry on `entry_closes_at` and on nothing else: four people can
 * arrange a game at six and play it at eight without ever filling a slot. So on the plan lead the
 * grid is one press away rather than absent, and the press is named for what it arrives at.
 * Strict one-action-per-state would buy a tidy table at the price of the app declining to hear the
 * one fact the whole loop exists to collect.
 *
 * ## The plan lead is three slots and two doors, and the screen still knows nothing
 *
 * [#410](https://github.com/Raketa02/Raketa/issues/410)'s design redraws the screen for the two
 * plan-lead rungs ([#414](https://github.com/Raketa02/Raketa/issues/414)): an eyebrow and **no
 * title**, the Now card at the top with its doors left off, the court's pairing — the forecast
 * block and the players card, filled by [#415](https://github.com/Raketa02/Raketa/issues/415)
 * with this feature's own `CourtPairing` — the chat's editable plan card, *We played* quiet
 * beneath it. So the one slot became **three** — `card`, `court`, `plan` — and every one of them
 * is a `ReactNode` this screen draws in order and cannot read, for the same reason the first was.
 * A **fourth**, `fill`, sits **directly under the card** since
 * [ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §4: the one act on the court itself this screen still draws — *Fill the seat*, a **challenge**
 * act reached from a game, composed onto this screen exactly as the plan is. It arrived as
 * `courtActs` with [#418](https://github.com/Raketa02/Raketa/issues/418), drawn last with *Leave
 * this game* and *Call it off*; both of those are gone — leaving is the Chats row's swipe alone,
 * and nobody calls a game off — and the fill moved to where the card that says *needs a player*
 * is. The eyebrow is `formatEyebrow`'s —
 * the format off the seats and the kind off the game, *Doubles · Counted* — because the card names
 * the people and the plan names the day, so `gameEyebrow`'s handles and *arranged n ago* would be
 * the same facts twice on one screen; it keeps the other arms. **The standing line and the
 * checklist go on this lead**: the card's bars and the counter carry both. The score lead keeps
 * today's screen whole — its standing line, its read-only plan child and its pinned footer — and
 * the result arms are untouched.
 *
 * **One door is in the scroll, and there is no pinned footer while the grid is closed.** The
 * design pins nothing on this lead, and a plan arm asks for nothing, so nothing on it wears the one
 * accent. *Open the chat* was the other door here, dark and full width, and it is gone
 * (ADR-0175 §4): the Now card's bubble and the Chats tab both reach the room, and this feature no
 * longer reaches `features/conversations` for the word, the route or the join — the seam
 * ADR-0149 §3 named is back to its one importer, `features/plans`. `We played` opens the grid
 * over the plan exactly as before, and the moment it is open the pinned footer is back with
 * *Send this score* and the way out.
 *
 * ## A booked game's result says who's here, caught at the court
 *
 * [#658](https://github.com/Raketa02/Raketa/issues/658) (ADR-0195 §3): on a **booked** game a *Who's
 * here* block (`WhosHere`) sits above the grid. In the first half hour it offers *Oscar isn't here
 * yet* about every other player and *Oscar is here* about anybody awaited — one press each, no
 * sheet, the phone's position read at the press — and after it says who came late and offers *Yes,
 * Oscar was here* about a late claim. **The reader's own act is pinned**: *I'm here* while they are
 * awaited, over the half hour on the clock, and *I was there* while they didn't come and their day
 * runs. Which game is booked, when its hour starts and at which club are the booking's to know, so
 * the composer hands them in (`booked`); a game nobody booked has no block because nobody does.
 */

import { useState, type ReactNode } from 'react';
import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { useCurrentUser } from '@/features/auth/types';
import { sportLabel } from '@/features/onboarding/types';
import { ShellScreen } from '@/features/shell/types';
import { StarCardSection } from '@/features/sportsmanship/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { openAppSettings } from '@/shared/lib/platform';
import { WE_PLAYED } from '@/shared/vocabulary/theActsWords';
import { Button, Note, theme } from '@/shared/ui';

import { attendanceBlock, type AttendanceRow } from '../domain/attendance';
import type { Game } from '../domain/game';
import {
  actsOffered,
  courtSizes,
  editingAct,
  resultArgument,
  scoresOnTable,
  sideOf,
  type EntryLead,
} from '../domain/resultArgument';
import { draftFrom, emptyDraft, readScore, sameScore, type ScoreDraft } from '../domain/score';
import {
  LocationAtTheTap,
  type AttendanceError,
  useClaimPresence,
  useConfirmPresence,
  useNoteArrival,
  useNoteNotHereYet,
} from '../hooks/useAttendance';
import { useAcceptResult, useGame, useStateResult } from '../hooks/useGames';

import { COUNTER_A11Y_LABEL, acceptLabel, submitLabelFor } from './gameAccessibility';
import { attendanceErrorMessage, gameErrorMessage, type AttendanceAct } from './gameErrorMessage';
import {
  ACCEPT_LABEL,
  CANCEL_LABEL,
  COUNTER_IS_THEIR_SCORE,
  COUNTER_LABEL,
  CORRECT_LABEL,
  IM_HERE_LABEL,
  I_WAS_THERE_LABEL,
  NOT_YOURS_LINE,
  OPEN_SETTINGS,
  SCORE_LEAD,
  SENDING_LABEL,
  STILL_ON_THE_TABLE,
  EVENING_FACTS,
  YOURS,
  clockLine,
  courtLine,
  endsAsAnEvening,
  formatEyebrow,
  gameEyebrow,
  resultBody,
  resultTitle,
  saysWhatItIsWorth,
  scoreProblemLine,
  settledScore,
  sideLabels,
  standingLine,
  submitLabel,
  worthLine,
} from './gamePresentation';
import { FactLine } from './FactLine';
import { ScoreEntry } from './ScoreEntry';
import { ScoreTable } from './ScoreTable';
import { WhosHere } from './WhosHere';

/**
 * **What a booked game's composer knows that the Game does not** (#560, #658) — handed in by
 * `proposals`, which holds the booking, and absent on a game nobody booked.
 */
export interface BookedFacts {
  /**
   * Re-read the booking's own reads once an act here has landed — Home's status and badge, and the
   * details this screen is pushed over — which this feature cannot name.
   */
  readonly reread: () => void;
  /**
   * **The booked hour's start** — what the first half hour, *isn't here yet*'s window, is measured
   * from. `GameSchema` carries no hour, and nothing on the wire carries the window before somebody
   * is tapped.
   */
  readonly startsAt: string;
  /** The club's name, for *You can say so only from Ogrody 33*. Absent where the read names none. */
  readonly club?: string;
}

export interface GameScreenProps {
  /** Validated by `schemas/routeParams.ts` before it reaches here; the route does that. */
  readonly gameId: string;
  /**
   * **The card at the top of the plan lead** — the Now card without its doors, drawn by whoever
   * composed this screen ([#414](https://github.com/Raketa02/Raketa/issues/414)). A slot, and
   * nothing about it is known here: it is `features/plans`' shell over a plan this feature may not
   * read. Drawn on the plan lead and nowhere else.
   */
  readonly card: ReactNode;
  /**
   * **The court's pairing — the forecast and the players — under the card.** A slot, so the
   * layout's order is decided once, and it is this feature's own `CourtPairing` that fills it
   * ([#415](https://github.com/Raketa02/Raketa/issues/415)) — composed by whoever composes the
   * screen rather than drawn here, because the faces on the players card come off the room join
   * that composition already holds for the card above, and this screen may not read that list.
   * Drawn on the plan lead and nowhere else, which is what keeps the read behind it off every
   * other arm.
   */
  readonly court: ReactNode;
  /**
   * **The plan, drawn by whoever composed this screen** — a slot, and nothing about it is known
   * here.
   *
   * `features/plans` fills it (ADR-0149 §2) and both surfaces that mount this screen hand the same
   * child down. **Required, and it is a `ReactNode` rather than an optional one on purpose**: the
   * score lead hands its worth line to the checklist inside this slot, so a caller who left it out
   * would take that sentence off the screen with it. A caller with genuinely nothing to render
   * passes `null` and says so.
   */
  readonly plan: ReactNode;
  /**
   * **What the entry arm leads with**, folded from the plan by whoever composed this screen.
   *
   * Required for the same reason the slot is: there is no honest default, and a screen that
   * guessed would open a score pad over a game six days away or bury the grid on the evening
   * somebody is trying to record.
   */
  readonly entryLead: EntryLead;
  /**
   * **The fill, directly under the card on the plan lead** — *Fill the seat*
   * ([#419](https://github.com/Raketa02/Raketa/issues/419), placed by ADR-0175 §4). A slot,
   * because it is a **challenge** act reached from a game (ADR-0162): the seat that fills is the
   * challenge's, so the control and its words are that feature's, and whoever composes this
   * screen hands it in — exactly as the plan is handed in, and for the same reason. Whether it
   * is drawn at all is the composer's rule (a seat open, and the agreed moment ahead, read off
   * the plan this screen may not know); `null` is a court with nothing to fill. Under the card
   * that says *needs a player*, and stood down with the doors while the grid is open.
   */
  readonly fill: ReactNode;
  /**
   * **A booked game's facts** (#560, #658) — how to re-read the booking, its hour and its club.
   * Present, the screen says who's here; absent, nobody booked it, and it has no hour anybody could
   * fail to come to.
   */
  readonly booked?: BookedFacts;
  /**
   * **PLAYED WITH, between the score and the star card** ([#754](https://github.com/Raketa02/Raketa/issues/754);
   * the friends screens §3). A slot, as the card and the plan are: the people and where the reader
   * stands with them are the booking's, and the rows are `friends`', so the composer hands it in and
   * this screen only says where it stands — under everything about the score, over *How were
   * they?*, on every arm. It draws itself or nothing (hidden once they are all friends); `null` is a
   * composer with nobody to list.
   */
  readonly playedWith: ReactNode;
}

export function GameScreen({
  gameId,
  card,
  court,
  plan,
  entryLead,
  fill,
  booked,
  playedWith,
}: GameScreenProps) {
  const { game, isPending, error } = useGame(gameId);
  const me = useCurrentUser().data?.id;

  if (game === undefined || me === undefined) {
    return (
      <ShellScreen title={resultTitle({ kind: 'not-yours' })} onBack={router.back}>
        {/* Three states with one sentence each, and none of them invents a fourth: the list is
            still coming, the read failed, or no game of yours has this address. */}
        {isPending ? null : error !== null ? (
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(error)}
          </Note>
        ) : (
          <Text style={s.line}>{NOT_YOURS_LINE}</Text>
        )}
      </ShellScreen>
    );
  }

  return (
    <Argument
      game={game}
      playerId={me}
      card={card}
      court={court}
      plan={plan}
      entryLead={entryLead}
      fill={fill}
      booked={booked}
      playedWith={playedWith}
    />
  );
}

/** No seat of this game is yours, so there is no court to describe and no side to draw from. */
const EMPTY_COURT = { ours: 0, theirs: 0 } as const;

function Argument({
  game,
  playerId,
  card,
  court,
  plan,
  entryLead,
  fill,
  booked,
  playedWith,
}: {
  readonly game: Game;
  readonly playerId: string;
  readonly card: ReactNode;
  readonly court: ReactNode;
  readonly plan: ReactNode;
  readonly entryLead: EntryLead;
  readonly fill: ReactNode;
  readonly booked: BookedFacts | undefined;
  readonly playedWith: ReactNode;
}) {
  const argument = resultArgument(game, playerId);
  // After any write here lands on a booked game, its booking's reads are read again — by the
  // mutation, so a write that waited out a lost connection still does it after the screen has gone.
  const afterAWrite = { reread: booked?.reread };
  const state = useStateResult(afterAWrite);
  const accept = useAcceptResult(afterAWrite);
  const notHere = useNoteNotHereYet(afterAWrite);
  const arrival = useNoteArrival(afterAWrite);
  const claim = useClaimPresence(afterAWrite);
  const confirm = useConfirmPresence(afterAWrite);

  /**
   * **Who's here** — the domain's to fold (`attendanceBlock`): a booked game's alone, measured from
   * the hour its booking handed in.
   */
  const block = attendanceBlock(game, playerId, booked);

  /**
   * **A new act clears what the last one was refused**, so the footer's one sentence is always
   * about the act just taken — six writes share it, and a refused tap must not stand over a score
   * that went through.
   */
  function clearRefusals(): void {
    for (const write of [state, accept, notHere, arrival, claim, confirm]) {
      if (write.isError) write.reset();
    }
  }

  /**
   * The grid, or nothing when it is closed. **Route-local**, because it is a draft rather than a
   * value: leaving this screen throws it away, which is the right answer for a score nobody sent.
   */
  const [draft, setDraft] = useState<ScoreDraft>();
  /** What is wrong with it — set on the press and cleared by the next key. */
  const [problem, setProblem] = useState<string>();

  const side = sideOf(game, playerId) ?? 'A';
  // Nought and nought when no seat is yours, which is the one arm that draws no court: the list
  // serves only your games, so this is a link that has gone stale rather than a game to describe.
  const { ours, theirs } =
    sideOf(game, playerId) === undefined ? EMPTY_COURT : courtSizes(game, side);
  const sides = sideLabels(ours);
  const sport = sportLabel(game.sport);

  // Both rules are the domain's: which controls exist, and what a grid opened here would send.
  const entryArm = argument.kind === 'awaiting-entry';
  /**
   * **The plan lead is the one arm the design redrew** (#414): the card, the court and the plan
   * over two doors, under an eyebrow with no title. Everything else is the screen as it was.
   */
  const planLead = entryArm && entryLead === 'the-plan';
  // **Not uppercased here.** `ScreenHeader` already draws an eyebrow uppercase in its style,
  // and a second copy in the string would reach a screen reader — which, where the eyebrow
  // names the people on the court, is a handle spelled out letter by letter. On the plan lead
  // it is the format and the kind: the card under it names the people.
  const eyebrow = planLead ? formatEyebrow(game) : gameEyebrow(sport, game, playerId);
  const acts = actsOffered(argument);
  const act = editingAct(argument);
  const entering = act === 'enter';
  /**
   * **The grid is the screen on the two arms that lead with the score, and a press away on the
   * two that lead with the plan** — §5.2's two landings inside one standing.
   *
   * Where it *is* the screen there is nothing behind it, so it never closes and no cancel is
   * drawn; where it opened over the plan there is, so `Leave it as it is` puts it back — which is
   * the rule this screen already applies to a correction and a counter.
   */
  const gridIsTheScreen = entering && (entryLead === 'the-score' || argument.kind === 'for-fun');
  const open = draft ?? (gridIsTheScreen ? emptyDraft(game.sport) : undefined);
  // The two scores on the table, and every control hangs off one of them rather than off the
  // state's name: an agreement is with `theirs`, a correction is of `ours`, and a counter
  // answers `theirs` with a score of our own. Either may be absent and both may be.
  const { ours: ourScore, theirs: theirScore } = scoresOnTable(argument);
  // What each table is called, and which of them is played down — both are statements about the
  // score rather than about the layout, so they are decided here rather than inside the render
  // tree. A score is quiet where it is context: beside a grid being typed into, and the reader's
  // own beside the other side's, where the one control on the screen agrees with the other one.
  const theirLead = ourScore === undefined ? SCORE_LEAD.only : SCORE_LEAD.theirs;
  const ourScoreIsContext = theirScore !== undefined || open !== undefined;

  function edit(next: ScoreDraft): void {
    setDraft(next);
    setProblem(undefined);
  }

  function send(): void {
    if (open === undefined || act === undefined) return;
    const reading = readScore(open);
    if (!reading.ok) {
      setProblem(scoreProblemLine(reading.problem, game.sport));
      return;
    }
    // The one refusal that is about the other side's score rather than this draft. A counter
    // that agrees with what it answers is the same score twice, which settles a day later what
    // *That's right* settles now (#654).
    if (
      act === 'counter' &&
      theirScore !== undefined &&
      sameScore(reading.score, theirScore.score)
    ) {
      setProblem(COUNTER_IS_THEIR_SCORE);
      return;
    }
    clearRefusals();
    state.mutate(
      { gameId: game.gameId, score: reading.score },
      { onSuccess: () => setDraft(undefined) },
    );
  }

  /** A row's tap: about that player, sent at once — the two at the club read the phone's position. */
  function tap(row: AttendanceRow): void {
    clearRefusals();
    const about = { gameId: game.gameId, playerId: row.playerId };
    switch (row.tap) {
      case 'not-here-yet':
        notHere.mutate(about);
        return;
      case 'here':
        arrival.mutate(about);
        return;
      case 'was-here':
        confirm.mutate(about);
        return;
      case undefined:
        return;
    }
  }

  /** The row whose tap is in flight. A paused confirmation is not in flight, and says so below. */
  const tappingAbout = [notHere, arrival, confirm].find(
    (write) => write.isPending && !write.isPaused && write.variables?.playerId !== playerId,
  )?.variables?.playerId;
  /** *I'm here* — the reader's own arrival, which is the same write about themselves. */
  const ownArrival = arrival.variables?.playerId === playerId;
  const arriving = ownArrival && arrival.isPending;

  /**
   * **What this evening is worth — drawn here on every arm but the entry one.**
   *
   * On the entry arm it is the checklist's third line, *cited rather than written*
   * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §5.3), and
   * the checklist is inside the slot. That is a statement about **where one sentence is printed**
   * and not about what fills the slot: this screen still holds no plan, and what it is avoiding is
   * printing `worthLine` twice in one view. **And it is said only where a score is up or stands**:
   * over an ending that took none it would be a second claim about the same evening.
   */
  const worth = saysWhatItIsWorth(argument) ? worthLine(game.kind) : undefined;
  /**
   * **The plan lead's two doors are in the scroll while the grid is closed**, and three things
   * follow from that one state: nothing is pinned, the doors are drawn, and the sentence about
   * what a score records waits for the grid it is about rather than sitting over a plan that is
   * still being agreed.
   */
  const doorsInTheScroll = planLead && open === undefined;
  // **On the plan lead the eyebrow says the format and the card draws the court**, so the shape
  // line would be the same fact a third time.
  const shape = planLead ? undefined : courtLine(ours, theirs);
  const rule = doorsInTheScroll
    ? undefined
    : resultBody(argument, { booked: booked !== undefined, readAt: game.readAt });
  /** The score that stands — a counted result, or a For fun game's — and what it said about you. */
  const settled = settledScore(argument);
  // The clock stands down while a score is being typed; which arms count down at all is
  // `clockLine`'s, and the entry's window is its standing line's clause rather than a clock.
  const clock = open === undefined ? clockLine(argument, game.readAt) : undefined;
  const sending = state.isPending && !state.isPaused;
  // Every act clears the last one's refusal before it is sent, so at most one is ever standing —
  // one sentence rather than six identical blocks that could never all be right.
  const refusal = refusalOf();
  function refusalOf(): { readonly line: string; readonly toSettings: boolean } | undefined {
    const atTheCourt: readonly (readonly [AttendanceAct, AttendanceError | null])[] = [
      ['not-here-yet', notHere.error],
      ['arrival', arrival.error],
      ['claim', claim.error],
      ['confirmation', confirm.error],
    ];
    for (const [act, error] of atTheCourt) {
      if (error === null) continue;
      return {
        line: attendanceErrorMessage(error, act, booked?.club),
        // A permission refused for good, and a phone sharing only a rough position, have one
        // remedy, and it is not a prompt.
        toSettings:
          error instanceof LocationAtTheTap &&
          (error.refusal === 'blocked' || error.refusal === 'rough'),
      };
    }
    const refused = state.error ?? accept.error;
    return refused === null ? undefined : { line: gameErrorMessage(refused), toSettings: false };
  }
  const paused = state.isPaused || accept.isPaused || claim.isPaused || confirm.isPaused;

  return (
    <ShellScreen
      // No title on the plan lead: the eyebrow is the heading there (10.3 as amended by #414).
      title={planLead ? undefined : resultTitle(argument)}
      eyebrow={eyebrow}
      onBack={router.back}
      // Nothing is pinned on the plan lead while the grid is closed — the design pins nothing,
      // and its two doors sit in the scroll under the plan. The grid opening brings the footer
      // back with the send and the way out, exactly as on every other arm.
      action={
        doorsInTheScroll ? undefined : (
          <Footer>
            {/* Part 11: the sentence sits **beside the act that is waiting**, which is here rather
              than in the page — a paused mutation is not in flight at all, and a note that
              scrolled would be a note about a control the player cannot see. */}
            {paused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}
            {refusal === undefined ? null : (
              <Note variant="coral" accessibilityRole="alert">
                {refusal.line}
              </Note>
            )}
            {refusal?.toSettings === true ? (
              <Button label={OPEN_SETTINGS} variant="secondary" onPress={openAppSettings} />
            ) : null}

            {open !== undefined && act !== undefined ? (
              <>
                <Button
                  label={submitLabel(act)}
                  accessibilityLabel={submitLabelFor(submitLabel(act), open, game.sport)}
                  onPress={send}
                  busy={sending}
                  busyLabel={SENDING_LABEL}
                />
                {gridIsTheScreen ? null : (
                  <Button
                    label={CANCEL_LABEL}
                    variant="secondary"
                    onPress={() => {
                      setDraft(undefined);
                      setProblem(undefined);
                    }}
                  />
                )}
              </>
            ) : (
              <>
                {/* No *We played* here any more: on the plan lead it is in the scroll under the
                  chat door, and on the score lead the grid is the screen, so no entry arm reaches
                  this branch with the grid closed. What is left is the answer arms' three acts. */}

                {/* Whether an agreement stands is the response's answer and `actsOffered`'s to
                  fold — `accept.isSuccess` only covers the round trip between the tap and the
                  list catching up, which is the echo and not the fact. */}
                {acts.includes('accept') && theirScore !== undefined && !accept.isSuccess ? (
                  <Button
                    label={ACCEPT_LABEL}
                    accessibilityLabel={acceptLabel({
                      score: theirScore.score,
                      sport: game.sport,
                      mine: side,
                      sides,
                    })}
                    onPress={() => {
                      clearRefusals();
                      accept.mutate(game.gameId);
                    }}
                    busy={accept.isPending && !accept.isPaused}
                    busyLabel={SENDING_LABEL}
                  />
                ) : null}
                {acts.includes('counter') && theirScore !== undefined ? (
                  <Button
                    label={COUNTER_LABEL}
                    accessibilityLabel={COUNTER_A11Y_LABEL}
                    variant="secondary"
                    onPress={() => edit(draftFrom(theirScore.score, game.sport))}
                  />
                ) : null}
                {acts.includes('correct') && ourScore !== undefined ? (
                  <Button
                    label={CORRECT_LABEL}
                    variant="secondary"
                    onPress={() => edit(draftFrom(ourScore.score, game.sport))}
                  />
                ) : null}
                {/* The reader's own act at the court (#658): *I'm here* while they are awaited,
                  *I was there* while they didn't come and their day runs. Whether either is
                  offered is the list's answer; `isSuccess` covers only the echo before it lands. */}
                {block.own === 'im-here' && !(ownArrival && arrival.isSuccess) ? (
                  <Button
                    label={IM_HERE_LABEL}
                    onPress={() => {
                      clearRefusals();
                      arrival.mutate({ gameId: game.gameId, playerId });
                    }}
                    busy={arriving}
                    busyLabel={SENDING_LABEL}
                  />
                ) : null}
                {block.own === 'i-was-there' && !claim.isSuccess ? (
                  <Button
                    label={I_WAS_THERE_LABEL}
                    onPress={() => {
                      clearRefusals();
                      claim.mutate(game.gameId);
                    }}
                    busy={claim.isPending && !claim.isPaused}
                    busyLabel={SENDING_LABEL}
                  />
                ) : null}
              </>
            )}
          </Footer>
        )
      }
    >
      {/* The standing line goes on the plan lead: the card's bars say what is agreed and the
          counter says how much, and the window left is a fact about a game whose day is here,
          which this lead's is not. */}
      {planLead ? null : <Text style={s.line}>{standingLine(argument, game.readAt)}</Text>}

      {/* The plan lead's head: the Now card without its doors, the fill directly under it where
          the card says *needs a player* (ADR-0175 §4), and the court's pairing under both. Three
          slots this screen draws in order and cannot read; the fill stands down with the doors
          while the grid is open. */}
      {planLead ? card : null}
      {planLead && doorsInTheScroll ? fill : null}
      {planLead ? court : null}

      {/* The plan, high on the page, because on two of the four entry arms it is what the player
          came for. It is drawn on this arm alone: the four confirm arms and the three endings are
          #314's, built and untouched, and a plan panel over a settled score would be an agreement
          about an evening that has already happened. */}
      {entryArm ? plan : null}

      {/* The one door on the plan lead: *We played*, quiet, in the scroll, because nothing is
          pinned here. It stands down while the grid is open, when the pinned footer carries the
          send and the way out. It is the domain's to offer, and it withholds it while a seat is
          open (#411 rule 5). */}
      {doorsInTheScroll && acts.includes('enter') ? (
        <Button
          label={WE_PLAYED}
          variant="secondary"
          onPress={() => edit(emptyDraft(game.sport))}
        />
      ) : null}

      {rule === undefined ? null : <Text style={s.body}>{rule}</Text>}
      {worth === undefined ? null : <Text style={s.body}>{worth}</Text>}
      {settled?.outcome === undefined ? null : <Text style={s.outcome}>{settled.outcome}</Text>}
      {ours === 0 || shape === undefined ? null : <Text style={s.body}>{shape}</Text>}

      {/* *Who's here* (#658) — above the grid and the scores: in the first half hour it is what a
          player at the court opens this screen for, and after it it says who came late. */}
      <WhosHere block={block} onTap={tap} tappingAbout={tappingAbout} />

      {endsAsAnEvening(argument) ? (
        <View style={s.facts}>
          {EVENING_FACTS.map((fact) => (
            <FactLine key={fact}>{fact}</FactLine>
          ))}
        </View>
      ) : null}

      {settled?.score === undefined ? null : (
        <View style={s.block}>
          <ScoreTable
            score={settled.score}
            sport={game.sport}
            mine={side}
            sides={sides}
            lead={settled.lead}
          />
        </View>
      )}

      {/* Our own score, quiet wherever it is context rather than the subject: beside the other
          side's on a disagreement, and beside the grid while it is being corrected. */}
      {ourScore === undefined ? null : (
        <View style={s.block}>
          <ScoreTable
            score={ourScore.score}
            sport={game.sport}
            mine={side}
            sides={sides}
            quiet={ourScoreIsContext}
            lead={SCORE_LEAD.ours}
          />
        </View>
      )}

      {/* The score being answered stays on screen beside the one being typed — variant C's own
          arrangement, and the thing it said only a route had room for. On a disagreement it is
          also the score the one control agrees with, which is why it is the loud one. The
          *THEIRS* heading is on this table alone now: it used to sit over whichever score was
          standing, which put it over the reader's **own** score while they corrected it. */}
      {theirScore === undefined ? null : (
        <View style={s.block}>
          {open === undefined ? null : <Text style={s.attrib}>{STILL_ON_THE_TABLE}</Text>}
          <ScoreTable
            score={theirScore.score}
            sport={game.sport}
            mine={side}
            sides={sides}
            quiet={open !== undefined}
            lead={theirLead}
          />
        </View>
      )}

      {/* The clock, big enough to read at arm's length: how long until silence makes a score the
          result, under the line that names the moment. It stands down while a score is typed. */}
      {clock === undefined ? null : (
        <View style={s.clock} accessible accessibilityLabel={`${clock.figure} ${clock.line}`}>
          <Text style={s.clockFigure}>{clock.figure}</Text>
          <Text style={s.clockLine}>{clock.line}</Text>
        </View>
      )}

      {open !== undefined ? (
        <View style={s.block}>
          {/* The heading exists to keep two tables apart, so it is drawn when there is another
              one — which is every state but the entry, where the grid is the whole screen. */}
          {ourScore === undefined && theirScore === undefined ? null : (
            <Text style={s.attrib}>{YOURS}</Text>
          )}
          <ScoreEntry draft={open} onChange={edit} sport={game.sport} mine={side} sides={sides} />
        </View>
      ) : null}

      {/* This one stays in the page, under the grid it is about — it names a cell. */}
      {problem === undefined ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {problem}
        </Note>
      )}

      {/* **PLAYED WITH** (#754) — the others on the game and where the reader stands with each,
          under everything about the score and over the question about how they were: the friends
          screens §3 put it between the two. The composer's slot; it draws itself or nothing. */}
      {playedWith}

      {/* **How were they** — last, and under everything this screen exists to say. The moment a
          player has to think about how an evening went is the moment they are looking at what
          came of it, which is this screen and not a row in a list.

          It is handed the game and asks nothing about the state: *whether* a card is open is the
          server's answer, and it is open only once the game has settled and only between the
          day after and a week later. So it draws on the endings and on nothing else — which is
          also every state where `actsOffered` is empty, so the card's own send is never a second
          control beside a pinned one. Nothing here re-derives any of that: a
          second spelling of that window would eventually disagree with the one the send is judged
          against, and it would disagree silently. */}
      <StarCardSection court={game} />
    </ShellScreen>
  );
}

/** The pinned slot's own column, so the sentences above the buttons keep the slot's gap. */
function Footer({ children }: { readonly children: ReactNode }) {
  return <View style={s.footer}>{children}</View>;
}

const s = StyleSheet.create({
  footer: { gap: theme.space.sm },
  line: { ...theme.type.h2, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.muted },
  outcome: { ...theme.type.cardTitle, color: theme.color.ink },
  block: { marginTop: theme.space.sm, gap: theme.space.xs },
  attrib: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  clock: { marginTop: theme.space.md, gap: theme.space.xxs },
  clockFigure: { ...theme.num.levelLarge, ...theme.tabular, color: theme.color.ink },
  clockLine: { ...theme.type.tiny, color: theme.color.muted },
  facts: { marginTop: theme.space.sm, gap: theme.space.xs },
});
