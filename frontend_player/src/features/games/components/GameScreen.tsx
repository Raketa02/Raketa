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
 * rather than a fact line, which is the whole of *silence confirming has to be visible before it
 * happens*.
 *
 * **The layout is that variant's, and so is most of the copy**: the clock block, the *still on
 * the table* / *yours* pair over the counter's grid, the two-button footer, and the fact list an
 * unscored evening ends on. What is rewritten is only what the model moved — there are no
 * absolute times, because this platform has no calendar. Names came back with the handle on a
 * seat, under `gamePresentation`'s rule: a person where a person acted, a side where a side did.
 *
 * ## One screen, seven states, and the state is derived
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
 * proposal's day starts whenever it lands, and an acceptance's grace runs from the score — so
 * both take the app's queue, and the sentence beside a paused control says it will resume.
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
 * **Two routes mount this one component** — `/games/[gameId]` under Now and
 * `/chats/conversation/[conversationId]/details` under Chats — so each lights its own column and
 * *back* is correct in both directions by construction. It is **not told which**, and that is the
 * point: a screen that knew its door would be a screen that could draw differently through one of
 * them.
 *
 * ## Three plan arms, and the one word that tells them apart
 *
 * §5.2 lands two different cards on two different things inside one standing: *Planning* and *Game
 * on* arrive at **the plan**, *Today* and *Needs result* at **the score grid**. The ladder that
 * tells them apart reads a plan, so the fold is `features/plans`' and what arrives here is
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
 * title**, the Now card at the top with its doors left off, a slot for the forecast and the players
 * ([#415](https://github.com/Raketa02/Raketa/issues/415) fills it), the chat's editable plan card,
 * *Open the chat* dark and full width, *We played* quiet beneath it. So the one slot became
 * **three** — `card`, `court`, `plan` — and every one of them is a `ReactNode` this screen draws in
 * order and cannot read, for the same reason the first was. The eyebrow is `formatEyebrow`'s —
 * the format off the seats and the kind off the game, *Doubles · Counted* — because the card names
 * the people and the plan names the day, so `gameEyebrow`'s handles and *arranged n ago* would be
 * the same facts twice on one screen; it keeps the other arms. **The standing line and the
 * checklist go on this lead**: the card's bars and the counter carry both. The score lead keeps
 * today's screen whole — its standing line, its read-only plan child and its pinned footer — and
 * the result arms are untouched.
 *
 * **The two doors are in the scroll, and there is no pinned footer while the grid is closed.** The
 * design pins nothing on this lead, and a plan arm asks for nothing, so nothing on it wears the one
 * accent: the chat door is 6.1's `dark` — *a filled action with no meaning attached*, and the first
 * one this app draws — which is exactly what a wide door on a screen that is not asking needs to
 * be. It is the same join ADR-0149 §3 settles — the player's rooms, read as such — drawn here
 * rather than in the plan child because the design puts it under the plan card and beside *We
 * played*, and it fails soft: no room, no door. **That widens the seam the ADR named** — *the game
 * screen reads a list belonging to a context it is forbidden to know about* — by one importer:
 * this feature now reaches `features/conversations` for the word, the route and the join, where
 * before only `features/plans` did on its behalf. Said here because the ADR asked the next person
 * to say so. `We played` opens the grid over the plan exactly as before, and the moment it is open
 * the pinned footer is back with *Send this score* and the way out.
 */

import { useState, type ReactNode } from 'react';
import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { useCurrentUser } from '@/features/auth/types';
import { CONVERSATION_ROUTE, OPEN_THE_CHAT, useChatDoor } from '@/features/conversations/types';
import { sportLabel } from '@/features/onboarding/types';
import { ShellScreen } from '@/features/shell/types';
import { StarCardSection } from '@/features/sportsmanship/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { WE_PLAYED } from '@/shared/vocabulary/theActsWords';
import { Button, Note, theme } from '@/shared/ui';

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
import { useAcceptResult, useGame, useStateResult } from '../hooks/useGames';

import { COUNTER_A11Y_LABEL, acceptLabel, submitLabelFor } from './gameAccessibility';
import { gameErrorMessage } from './gameErrorMessage';
import {
  ACCEPT_LABEL,
  CANCEL_LABEL,
  COUNTER_IS_THEIR_SCORE,
  COUNTER_LABEL,
  CORRECT_LABEL,
  NOT_YOURS_LINE,
  SCORE_LEAD,
  SENDING_LABEL,
  STILL_ON_THE_TABLE,
  UNSCORED_FACTS,
  YOURS,
  clockLine,
  courtLine,
  formatEyebrow,
  gameEyebrow,
  outcomeLine,
  resultBody,
  resultTitle,
  scoreProblemLine,
  sideLabels,
  standingLine,
  submitLabel,
  worthLine,
} from './gamePresentation';
import { ScoreEntry } from './ScoreEntry';
import { ScoreTable } from './ScoreTable';

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
   * **The court's pairing — the forecast and the players — under the card.** A slot
   * [#415](https://github.com/Raketa02/Raketa/issues/415) fills; `null` until it does, and stated
   * as a prop now so the layout's order is decided once. Drawn on the plan lead and nowhere else.
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
}

export function GameScreen({ gameId, card, court, plan, entryLead }: GameScreenProps) {
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
}: {
  readonly game: Game;
  readonly playerId: string;
  readonly card: ReactNode;
  readonly court: ReactNode;
  readonly plan: ReactNode;
  readonly entryLead: EntryLead;
}) {
  const argument = resultArgument(game, playerId);
  const state = useStateResult();
  const accept = useAcceptResult();

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
  const gridIsTheScreen = entering && entryLead === 'the-score';
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
    // that agrees with what it answers is a second proposal nobody will accept, and it ends the
    // game unscored between two people who agreed.
    if (
      act === 'counter' &&
      theirScore !== undefined &&
      sameScore(reading.score, theirScore.score)
    ) {
      setProblem(COUNTER_IS_THEIR_SCORE);
      return;
    }
    state.mutate(
      { gameId: game.gameId, score: reading.score },
      { onSuccess: () => setDraft(undefined) },
    );
  }

  /**
   * **What this evening is worth — drawn here on every arm but the entry one.**
   *
   * On the entry arm it is the checklist's third line, *cited rather than written*
   * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §5.3), and
   * the checklist is inside the slot. That is a statement about **where one sentence is printed**
   * and not about what fills the slot: this screen still holds no plan, and what it is avoiding is
   * printing `worthLine` twice in one view.
   */
  const worth = entryArm ? undefined : worthLine(game.kind);
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
  const rule = doorsInTheScroll ? undefined : resultBody(argument);
  const outcome = argument.kind === 'confirmed' ? outcomeLine(argument.outcome) : undefined;
  // The entry window is the standing line's clause on all four entry arms, so the block never
  // draws over one: a 40pt figure counting down to *recorded as one that never happened* is not
  // what a game six days away is about, and on the two score-led arms the grid is over it anyway.
  const clock = open === undefined && !entryArm ? clockLine(argument, game.readAt) : undefined;
  const sending = state.isPending && !state.isPaused;
  // Two mutations, one at a time by construction — the grid is either open or it is not — so one
  // sentence rather than two identical blocks that could never both be right.
  const failure = state.error ?? accept.error;
  const paused = state.isPaused || accept.isPaused;

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
            {failure === null ? null : (
              <Note variant="coral" accessibilityRole="alert">
                {gameErrorMessage(failure)}
              </Note>
            )}

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
                    onPress={() => accept.mutate(game.gameId)}
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

      {/* The plan lead's head: the Now card without its doors, and the court's pairing under it.
          Two slots this screen draws in order and cannot read. */}
      {planLead ? card : null}
      {planLead ? court : null}

      {/* The plan, high on the page, because on two of the four entry arms it is what the player
          came for. It is drawn on this arm alone: the four confirm arms and the three endings are
          #314's, built and untouched, and a plan panel over a settled score would be an agreement
          about an evening that has already happened. */}
      {entryArm ? plan : null}

      {/* The two doors, on the plan lead: the chat's, dark and full width, and *We played* quiet
          beneath it — in the scroll, because nothing is pinned here. Both stand down while the
          grid is open, when the pinned footer carries the send and the way out. */}
      {doorsInTheScroll ? (
        <>
          <OpenTheChat challengeId={game.challengeId} />
          {acts.includes('enter') ? (
            <Button
              label={WE_PLAYED}
              variant="secondary"
              onPress={() => edit(emptyDraft(game.sport))}
            />
          ) : null}
        </>
      ) : null}

      {rule === undefined ? null : <Text style={s.body}>{rule}</Text>}
      {worth === undefined ? null : <Text style={s.body}>{worth}</Text>}
      {outcome === undefined ? null : <Text style={s.outcome}>{outcome}</Text>}
      {ours === 0 || shape === undefined ? null : <Text style={s.body}>{shape}</Text>}

      {argument.kind === 'unscored' ? (
        <View style={s.facts}>
          {UNSCORED_FACTS.map((fact) => (
            <View key={fact} style={s.factRow}>
              <View style={s.factDot} />
              <Text style={s.factText}>{fact}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {argument.kind === 'confirmed' && argument.score !== undefined ? (
        <View style={s.block}>
          <ScoreTable
            score={argument.score}
            sport={game.sport}
            mine={side}
            sides={sides}
            lead={SCORE_LEAD.agreed}
          />
        </View>
      ) : null}

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

      {/* The clock, big enough to read at arm's length. It is the whole of *silence confirming
          is visible before it happens*, and it stands down while a score is being typed. */}
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

      {/* **How were they** — last, and under everything this screen exists to say. The moment a
          player has to think about how an evening went is the moment they are looking at what
          came of it, which is this screen and not a row in a list.

          It is handed the game and asks nothing about the state: *whether* a card is open is the
          server's answer, and it is open only once the result has settled and only between the
          day after and a week later. So it draws on `confirmed` and `unscored` and on nothing
          else — which is also every state where `actsOffered` is empty, so the card's own send is
          never a second control beside a pinned one. Nothing here re-derives any of that: a
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

/**
 * **The chat door on the plan lead** — dark, full width, and the join ADR-0149 §3 settles: the
 * player's rooms, read as such, over the list the Chats tab fetches anyway. **Fails soft**: a
 * conversation opens on the first acceptance and is destroyed when the episode ends, so no room
 * draws no door rather than a dead one. Its own component so the join is read exactly where the
 * door is drawn, and `Argument` holds no hook for a control three of its arms never draw; the
 * list itself is one Query and the composition already reads it for the card's faces, so this
 * costs no request of its own.
 */
function OpenTheChat({ challengeId }: { readonly challengeId: string }) {
  const conversationId = useChatDoor(challengeId);

  if (conversationId === undefined) return null;

  return (
    <Button
      label={OPEN_THE_CHAT}
      variant="dark"
      size="lg"
      onPress={() => router.push({ pathname: CONVERSATION_ROUTE, params: { conversationId } })}
    />
  );
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
  factRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  factDot: {
    width: theme.space.xxs,
    height: theme.space.xxs,
    borderRadius: theme.space.xxs,
    backgroundColor: theme.color.muted,
  },
  factText: { ...theme.type.tiny, color: theme.color.ink, flex: 1 },
});
