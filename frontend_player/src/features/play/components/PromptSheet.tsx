/**
 * **`SH.saveav`** — the sheet that lets a player answer a question the platform has been
 * raising with nowhere to put the answer ([#275](https://github.com/Raketa02/Raketa/issues/275)).
 *
 * One sheet for all four prompts, keyed per prompt, with **no string of its own**: the title,
 * the body, the closer, the suppression sentence and both control names come off
 * `promptPresentation` through §1's code → message mechanism, and a fifth prompt fails to
 * compile there rather than drawing an unlabelled button here.
 *
 * ## It never blocks, and that is structural rather than sequenced
 *
 * The prompts ride on the search's own response, so by the time this is on screen the search
 * has already run — *"either way the search runs now"* is arithmetic and not a promise a
 * component keeps ([#226](https://github.com/Raketa02/Raketa/issues/226) §6). What it stands
 * in front of is the screen's arrangement and never this one's: it reports what was answered
 * and the screen decides where that goes.
 *
 * **Three surfaces raise prompts and only one of them pushes anywhere**
 * ([#287](https://github.com/Raketa02/Raketa/issues/287)). On Find a game the sheet stands
 * between the latch lifting and the court being pushed. ⚡ lands on the court the player is
 * already looking at and a deal replaces the card in place, so on those two it stands in front
 * of the answer that is already there, and `AfterThePrompt` can only ever be *carry-on* —
 * because the one prompt whose answer is the other value is the one those two surfaces drop.
 *
 * ## Dismissal is a decline
 *
 * The scrim, the close control and the Android back gesture all answer *not now*, and the row
 * is written exactly as the button writes it. Walking away from a sheet whose footer promises
 * the search has already run is indistinguishable in intent from pressing *not now*, and the
 * alternative reproduces the defect this was built against — on the two prompts whose
 * condition never stops being true, an unanswered question is asked again forever
 * ([#237](https://github.com/Raketa02/Raketa/issues/237) §5).
 *
 * **And the player is told**, because thirty days of silence nobody mentions is a hidden
 * mechanism — ADR-0128's own instinct. The sentence is the copy deck's, and its absence on
 * `KEEP_THESE_TIMES` is a typed absence rather than a string somebody forgot.
 *
 * ## The two answers fail differently, and only one of them has anywhere to say so
 *
 * A *yes* is a write the player is waiting on: it keeps the sheet up, draws its refusal over
 * the control that failed, and the retry is that control. A *not now* closes the sheet as it
 * is written, because nothing reads a decline back — a failed one costs the question being
 * asked again, which is the state the app was in before the row existed.
 *
 * ## What it draws that is not words
 *
 * `KEEP_THESE_TIMES` gets **6.8's diff variant** of the same grid the search screen edits — a
 * plus on what the search added, a dash on what it dropped — because the sentence beside it
 * names those two marks and a sheet that named them without drawing them would be describing
 * marks that are not on the screen. A **cleared week** draws as every profile cell dashed,
 * which is §12's second body as a picture.
 */

import { useRef } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { AvailabilityGrid, BottomSheet, Button, Note, theme, type FocusTarget } from '@/shared/ui';
import { dayPartHead } from '@/shared/vocabulary/availabilityPresentation';
import type { Sport } from '@/shared/vocabulary/sport';
import { DAY_PARTS } from '@/shared/vocabulary/week';

import { acceptWritesTheValue, type RaisedPrompt } from '../domain/raisedPrompt';
import { useAnswerPrompt } from '../hooks/useAnswerPrompt';

import { playErrorMessage } from './playErrorMessage';
import { promptControls, promptCopy } from './promptPresentation';
import { weekDiffRows } from './weekDiffPresentation';

/**
 * What the player asked for next — **the whole of what the screen behind needs to know.**
 *
 * Three of the four prompts are answered where they stand and the court is what comes next.
 * The fourth is `REFRESH_YOUR_TIMES`, whose *yes* is a request to go and edit the week rather
 * than a value to write: it carries none, and it is only ever raised on a week the profile
 * already holds. So its accept hands the player back to the grid on the screen underneath,
 * and this is where that is decided, beside the button that says it.
 */
export type AfterThePrompt = 'carry-on' | 'back-to-the-week';

export interface PromptSheetProps {
  readonly visible: boolean;
  /** The question, with the values its sentence quotes and its grid draws. */
  readonly raised: RaisedPrompt;
  /**
   * Whose screen raised it. **Not the key a suppression is stored under** — a radius and a
   * week are one fact each for the whole player — but the decline route takes it on every
   * prompt, and only the declaration is per sport.
   */
  readonly sport: Sport;
  /**
   * Answered, dismissed or accepted: the sheet is done, and this says where to go. **Called
   * at most once** — see the guard inside.
   */
  readonly onAnswered: (next: AfterThePrompt) => void;
  /**
   * Where focus goes when the sheet closes — **and it is per surface, because the thing the
   * question is about is not on all three of them.**
   *
   * Part 13's third modal obligation is focus returned to the control that opened it, and this
   * sheet was opened by an *answer* rather than by a press: there is no trigger. On Find a
   * game the week grid is the honest target — it is what three of the four prompts are about
   * and what the fourth's *yes* is a request for — and on the deck it is the card the deal put
   * on screen, which is where the player is.
   *
   * On the builder it is **⚡**, which is genuinely the control that raised it — and which
   * that same act unmounts where it fills the court, replacing the two ways of filling one
   * with the send. `moveAccessibilityFocus` is silent on an empty ref, so that case lands a
   * listener on the platform's own default rather than on the app's one irreversible act,
   * which is the right nothing ([#287](https://github.com/Raketa02/Raketa/issues/287)).
   *
   * **Optional because absent is a real answer**, on `WhyFitSheet`'s own precedent one
   * directory over, and because `BottomSheet` beneath already takes none.
   */
  readonly returnFocusTo?: FocusTarget;
}

export function PromptSheet({
  visible,
  raised,
  sport,
  onAnswered,
  returnFocusTo,
}: PromptSheetProps) {
  const answer = useAnswerPrompt();
  const copy = promptCopy(raised);
  const controls = promptControls(raised.prompt);

  /**
   * **One question, one answer**, whichever control gave it.
   *
   * A *yes* is a request the player waits on, and the sheet is dismissible while it is in
   * flight — an offline write is *paused* rather than pending, and a modal that could not be
   * closed until the connection came back would be the dead end `SearchingLatch` exists to
   * dissolve. So both paths can reach here, and the second one has to be a no-op: reporting
   * twice would answer one question two ways.
   *
   * It is a ref rather than state because nothing renders from it, and the sheet is mounted
   * per search — see the `key` at the call site — so it cannot outlive its own question.
   */
  const answered = useRef(false);

  const finish = (next: AfterThePrompt) => {
    if (answered.current) return;
    answered.current = true;
    onAnswered(next);
  };

  // The one prompt whose *yes* writes nothing is asking for the week, and the week is on the
  // screen underneath. Which prompt that is, is `domain/raisedPrompt`'s to say.
  const accepted: AfterThePrompt = acceptWritesTheValue(raised.prompt)
    ? 'carry-on'
    : 'back-to-the-week';

  /**
   * *Not now* — written as the sheet closes, on the three prompts a decline buys silence on.
   *
   * **A *yes* already sent is the answer**, so dismissing after one writes no decline: the
   * write is on its way, and a row here would give one question both answers. Walking away
   * before one is the decline this sheet's whole argument rests on.
   */
  const dismiss = () => {
    if (!answer.accept.isPending) answer.decline.mutate({ raised, sport });
    finish('carry-on');
  };

  const paused = answer.accept.isPaused;

  return (
    <BottomSheet
      visible={visible}
      // The scrim, the close control and Android's back gesture, all three of which are this
      // sheet's *non-committal* option — and here that option is itself an answer.
      onClose={dismiss}
      title={copy.title}
      closeLabel={controls.close}
      returnFocusTo={returnFocusTo}
    >
      {raised.prompt === 'KEEP_THESE_TIMES' ? (
        <AvailabilityGrid
          variant="diff"
          rows={weekDiffRows(raised.week, raised.profileWeek)}
          columnHeads={DAY_PARTS.map(dayPartHead)}
        />
      ) : null}

      <Text style={s.body}>{copy.body}</Text>

      {/* The refusal belongs over the control that failed, and the retry is that control:
          nothing was written, so pressing it again is the same act rather than a second one. */}
      {answer.accept.error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {playErrorMessage(answer.accept.error)}
        </Note>
      ) : null}

      {/* Paused, not pending: `networkMode: 'online'` holds the write until the connection
          returns, so a spinner here would be a wait with nothing behind it. */}
      {paused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

      <View style={s.answers}>
        <Button
          label={controls.accept}
          size="lg"
          busy={answer.accept.isPending && !paused}
          disabled={answer.accept.isPending}
          onPress={() =>
            answer.accept.mutate({ raised, sport }, { onSuccess: () => finish(accepted) })
          }
        />
        <Button
          label={controls.decline}
          variant="secondary"
          disabled={answer.accept.isPending}
          onPress={dismiss}
        />
      </View>

      {/* §F2's closer, and — where declining buys anything — what *not now* costs. The second
          sentence is absent rather than blank on the one prompt that suppresses nothing. */}
      <Text style={s.closing}>
        {copy.suppression === undefined ? copy.closer : `${copy.closer} ${copy.suppression}`}
      </Text>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  body: { ...theme.type.tiny, color: theme.color.ink, paddingTop: theme.space.xs },
  answers: { paddingTop: theme.space.sm, gap: theme.space.xs },
  closing: {
    ...theme.type.tiny,
    color: theme.color.muted,
    textAlign: 'center',
    paddingTop: theme.space.sm,
  },
});
