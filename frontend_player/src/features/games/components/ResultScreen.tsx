/**
 * **The result conversation, on a screen of its own.**
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
 * absolute times, because this platform has no calendar, and nobody is named, because the games
 * contract carries no handle.
 *
 * ## One screen, seven states, and the state is derived
 *
 * `domain/conversation.ts` decides which; nothing here reads a standing directly. That matters
 * most at the two states that look alike and are not: **a correction and a counter are the same
 * request** and completely different news, so the screen that offers one never offers the other,
 * and the words for each say which it is before the tap.
 *
 * ## The grid opens over what is already on screen, and closes on the answer
 *
 * On a game nobody has claimed, there is nothing to open over — the grid *is* the screen. On a
 * standing score it opens **pre-loaded with the score it answers**, because a real disagreement
 * is usually one digit, and an unchanged one is refused here rather than paid for a day later:
 * two matching scores nobody accepts still leave the game unscored.
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
 */

import { useState, type ReactNode } from 'react';
import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { useCurrentUser } from '@/features/auth/types';
import { sportLabel } from '@/features/onboarding/types';
import { ShellScreen } from '@/features/shell/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import {
  actsOffered,
  courtSizes,
  editingAct,
  resultConversation,
  sideOf,
} from '../domain/conversation';
import type { Game } from '../domain/game';
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
  SENDING_LABEL,
  STILL_ON_THE_TABLE,
  UNSCORED_FACTS,
  YOURS,
  acceptedLine,
  clockLine,
  courtLine,
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

export interface ResultScreenProps {
  /** Validated by `schemas/routeParams.ts` before it reaches here; the route does that. */
  readonly gameId: string;
}

export function ResultScreen({ gameId }: ResultScreenProps) {
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

  return <Conversation game={game} playerId={me} />;
}

/** No seat of this game is yours, so there is no court to describe and no side to draw from. */
const EMPTY_COURT = { ours: 0, theirs: 0 } as const;

function Conversation({ game, playerId }: { readonly game: Game; readonly playerId: string }) {
  const conversation = resultConversation(game, playerId);
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
  const acts = actsOffered(conversation);
  const act = editingAct(conversation);
  const entering = act === 'enter';
  const open = draft ?? (entering ? emptyDraft(game.sport) : undefined);
  const standing =
    conversation.kind === 'ours-stands' || conversation.kind === 'theirs-stands'
      ? conversation.proposal
      : undefined;

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
    if (act === 'counter' && standing !== undefined && sameScore(reading.score, standing.score)) {
      setProblem(COUNTER_IS_THEIR_SCORE);
      return;
    }
    state.mutate(
      { gameId: game.gameId, score: reading.score },
      { onSuccess: () => setDraft(undefined) },
    );
  }

  const body = resultBody(conversation);
  const worth = worthLine(game.kind);
  const outcome = conversation.kind === 'confirmed' ? outcomeLine(conversation.outcome) : undefined;
  const clock = open === undefined ? clockLine(conversation, game.readAt) : undefined;
  const sending = state.isPending && !state.isPaused;
  // Two mutations, one at a time by construction — the grid is either open or it is not — so one
  // sentence rather than two identical blocks that could never both be right.
  const failure = state.error ?? accept.error;
  const paused = state.isPaused || accept.isPaused;

  return (
    <ShellScreen
      title={resultTitle(conversation)}
      eyebrow={gameEyebrow(sport, game).toUpperCase()}
      onBack={router.back}
      action={
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
              {entering ? null : (
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
              {/* An acceptance is offered until this mount has made one. It cannot be hidden
                  after a remount — nothing on the response says one happened — which is the
                  second gap `domain/conversation.ts` records. */}
              {acts.includes('accept') && standing !== undefined && !accept.isSuccess ? (
                <Button
                  label={ACCEPT_LABEL}
                  accessibilityLabel={acceptLabel({
                    score: standing.score,
                    sport: game.sport,
                    mine: side,
                    sides,
                  })}
                  onPress={() => accept.mutate(game.gameId)}
                  busy={accept.isPending && !accept.isPaused}
                  busyLabel={SENDING_LABEL}
                />
              ) : null}
              {acts.includes('counter') && standing !== undefined ? (
                <Button
                  label={COUNTER_LABEL}
                  accessibilityLabel={COUNTER_A11Y_LABEL}
                  variant="secondary"
                  onPress={() => edit(draftFrom(standing.score, game.sport))}
                />
              ) : null}
              {acts.includes('correct') && standing !== undefined ? (
                <Button
                  label={CORRECT_LABEL}
                  variant="secondary"
                  onPress={() => edit(draftFrom(standing.score, game.sport))}
                />
              ) : null}
            </>
          )}
        </Footer>
      }
    >
      <Text style={s.line}>{standingLine(conversation, game.readAt)}</Text>
      {body === undefined ? null : <Text style={s.body}>{body}</Text>}
      {worth === undefined ? null : <Text style={s.body}>{worth}</Text>}
      {outcome === undefined ? null : <Text style={s.outcome}>{outcome}</Text>}
      {ours === 0 ? null : <Text style={s.body}>{courtLine(ours, theirs)}</Text>}

      {conversation.kind === 'unscored' ? (
        <View style={s.facts}>
          {UNSCORED_FACTS.map((fact) => (
            <View key={fact} style={s.factRow}>
              <View style={s.factDot} />
              <Text style={s.factText}>{fact}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {conversation.kind === 'confirmed' && conversation.score !== undefined ? (
        <View style={s.block}>
          <ScoreTable
            score={conversation.score}
            sport={game.sport}
            mine={side}
            sides={sides}
            lead="The agreed score"
          />
        </View>
      ) : null}

      {/* The score being answered stays on screen beside the one being typed — variant C's own
          arrangement, and the thing it said only a route had room for. */}
      {standing !== undefined ? (
        <View style={s.block}>
          {open === undefined ? null : <Text style={s.attrib}>{STILL_ON_THE_TABLE}</Text>}
          <ScoreTable
            score={standing.score}
            sport={game.sport}
            mine={side}
            sides={sides}
            quiet={open !== undefined}
            lead={conversation.kind === 'ours-stands' ? 'Your score' : 'The score on the table'}
          />
        </View>
      ) : null}

      {/* The clock, big enough to read at arm's length. It is the whole of *silence confirming
          is visible before it happens*, and it stands down while a score is being typed. */}
      {clock === undefined ? null : (
        <View style={s.clock} accessible accessibilityLabel={`${clock.figure} ${clock.line}`}>
          <Text style={s.clockFigure}>{clock.figure}</Text>
          <Text style={s.clockLine}>{clock.line}</Text>
        </View>
      )}

      {accept.isSuccess && standing !== undefined ? (
        <Note variant="mint">{acceptedLine(standing.settlesAt, game.readAt)}</Note>
      ) : null}

      {open !== undefined ? (
        <View style={s.block}>
          {standing === undefined ? null : <Text style={s.attrib}>{YOURS}</Text>}
          <ScoreEntry draft={open} onChange={edit} sport={game.sport} mine={side} sides={sides} />
        </View>
      ) : null}

      {/* This one stays in the page, under the grid it is about — it names a cell. */}
      {problem === undefined ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {problem}
        </Note>
      )}
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
  factRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  factDot: {
    width: theme.space.xxs,
    height: theme.space.xxs,
    borderRadius: theme.space.xxs,
    backgroundColor: theme.color.muted,
  },
  factText: { ...theme.type.tiny, color: theme.color.ink, flex: 1 },
});
