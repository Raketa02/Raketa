/**
 * **The finish** — the control that ends onboarding's second part, and every state around it.
 *
 * It is drawn by the last step, which is *Who you play with* since the radius and the
 * proposals question left the part ([#582](https://github.com/Raketa02/Raketa/issues/582)).
 * It used to be written inline on the proposals step; it is its own component now because
 * none of it is about the question the last step asks. It would say the same words on
 * whichever step ended the part, and the step that draws it should read as that step.
 *
 * ## This is where the part is written, and it is the only place that is
 *
 * Every answer went into the client-held draft, and the finish sends **the whole of it in one
 * request** ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 * Not six writes: a partial commit — the tags saved and the week lost — is the worst outcome
 * this part has available to it.
 *
 * What that costs is states only the last step can have. **A commit that did not land**
 * leaves the player exactly here, with the draft intact and the control that failed as the
 * retry, and nothing anywhere claiming the account was set up. **A commit with an answer
 * still missing** cannot be sent at all, and the one it is realistically short of is the
 * area — the location step names that cost when a player passes it, and this is where it is
 * collected, with the way back one press away.
 *
 * There is a third, and it is the seam between the two: **a failure whose code names a
 * step.** The commit re-validates every rule a picker enforced, so `weekly_hours_empty` can
 * arrive from a build that predates the week's floor or from a replayed request — and *try
 * again* is then the one sentence that is not true, because the identical body fails
 * identically. It is drawn as the failure it is, in the words of the answer it names, with
 * the same control back to the step that takes it. `intro_not_admitted` is the other code
 * that names a step, and the one this screen will actually meet: the fence on the line is the
 * server's pattern, so a phone number typed on step two is refused here, four screens later,
 * in the sentence its reason names and with *Change your intro* under it (ADR-0170 §2). The
 * finish stays pressable, exactly as it does after any other correctable refusal; what
 * changes is that the screen no longer promises that pressing it is enough.
 *
 * The sequencing is `useCommitProfile`'s and the rule about what a complete part is is
 * `readyToCommit`'s. What is left here is what a player sees and touches.
 */

import { useRouter } from 'expo-router';

import { recoveryMessage } from '@/shared/errors';
import { Button, Note } from '@/shared/ui';

import { mayFinish, type CommitStanding } from '../domain/profileCommit';
import { useCommitProfile } from '../hooks/useCommitProfile';

import {
  COMMIT_FAILED_BODY,
  COMMIT_FAILED_TITLE,
  FINISHING_WORD,
  FINISH_HINT,
  FINISH_LABEL,
  UPLOADING_BODY,
  UPLOADING_HINT,
  UPLOADING_TITLE,
  answerStillWanted,
  stepTheCommitRefused,
} from './commitPresentation';
import { SOCIAL_STEP_PATH, pathThatAsks } from './socialStepRoutes';

/**
 * Where the steps lead once the server has it: **Home**
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §1,
 * [#730](https://github.com/Raketa02/Raketa/issues/730)). *What Raketa keeps*, which stood here,
 * recorded nothing and went; the commit marks the profile on the player read, so the gate lets
 * her through to the app's root, which is Home.
 *
 * A route literal rather than an import, and that is the boundary working: the app's root is
 * the gate's, and this feature owns the profile rather than the flow around it. Written here,
 * beside the one press that goes there, rather than in `socialStepRoutes`: that table is the
 * six steps, and the six steps stop before this.
 */
const AFTER_THE_STEPS = '/';

/**
 * Why the finish will not move, for whoever cannot see that it will not.
 *
 * Three closed reasons and they are genuinely different: an answer an earlier step asks for, a
 * photo still arriving, and the question on the step drawing this. Only the last is that
 * step's to word — reaching for its hint in either of the other two would tell a player to
 * do something they have already done.
 */
function finishHint(
  standing: CommitStanding['kind'],
  stepHint: string | undefined,
  unansweredHint: string,
): string {
  if (standing === 'uploading') return UPLOADING_HINT;
  if (standing !== 'incomplete') return FINISH_HINT;
  return stepHint ?? unansweredHint;
}

export interface ProfileFinishProps {
  /**
   * What the closed finish says when the only answer still outstanding is the one the step
   * drawing it asks — in that step's own words, because only that step knows them.
   */
  readonly unansweredHint: string;
}

export function ProfileFinish({ unansweredHint }: ProfileFinishProps) {
  const router = useRouter();
  const { standing: commit, finish } = useCommitProfile();

  /**
   * What the finish is waiting for, if anything — an answer a step **behind** this one asks.
   * The question on this step is never in it: a player short of that one is standing on the
   * controls that give it, and is told so by `unansweredHint`.
   */
  const wanted = answerStillWanted(commit.kind === 'incomplete' ? commit.missing : []);
  /**
   * The same question, asked by the server instead of by the draft — or a line the server
   * would not admit.
   *
   * **The commit re-validates what the pickers already enforced** — a disabled control is
   * absent from a replayed request and from an older build — so a refusal naming an answer
   * is a real thing to render rather than an impossible one. When it arrives it replaces
   * the generic *try again*: retrying the identical body fails identically, and what the
   * player needs is the step that takes the answer. The intro's refusal is the one the
   * client genuinely cannot see coming — the fence is the server's pattern — and it is drawn
   * the same way: the reason's sentence, and the way back to the step.
   */
  const refused = commit.kind === 'failed' ? stepTheCommitRefused(commit.error) : undefined;
  /**
   * Whether the finish takes a press. **The rule is `mayFinish`'s**, and the only thing left
   * here is drawing it.
   *
   * It deliberately stays open while a commit is in flight: the design system is explicit
   * that *a busy button is not a disabled button*, and a control announcing itself disabled
   * with a hint asking for an answer already given would describe a screen that does not
   * exist.
   */
  const open = mayFinish(commit);

  return (
    <>
      {/* The failure, and it is `coral` and an alert because it is a status about something
          the player just did rather than an explanation of the product. It says what did not
          happen and that nothing was lost — never that setting up worked, which is the one
          claim a failed commit must not make. */}
      {commit.kind === 'failed' ? (
        <Note variant="coral" title={COMMIT_FAILED_TITLE} accessibilityRole="alert">
          {/* A refusal that names an answer says so instead of `recoveryMessage`'s category
              sentence and the promise that pressing again is enough. Both would be untrue
              here: the same body fails the same way, and the thing that fixes it is a step
              behind this one. Nothing was lost either way. */}
          {refused === undefined
            ? `${recoveryMessage(commit.error)} ${COMMIT_FAILED_BODY}`
            : refused.body}
        </Note>
      ) : null}

      {/* An answer the commit cannot do without, and the way back to the step that asks it.
          `amber` rather than `coral`: nothing has gone wrong and nothing is lost — this is a
          step still to be taken, and it is one press away. */}
      {wanted !== undefined ? (
        <>
          <Note variant="amber" title={wanted.copy.title}>
            {wanted.copy.body}
          </Note>
          <Button
            label={wanted.copy.label}
            variant="secondary"
            size="lg"
            onPress={() => router.replace(pathThatAsks(wanted.answer))}
          />
        </>
      ) : null}

      {/* The way back, for a refusal. The coral note above already carries the words — a
          second one under it would say the same thing twice — so what is left is the
          control, which is the half a player cannot do without. */}
      {refused !== undefined ? (
        <Button
          label={refused.label}
          variant="secondary"
          size="lg"
          onPress={() => router.replace(SOCIAL_STEP_PATH[refused.step])}
        />
      ) : null}

      {/* A photo the player watched go up, still going. There is nothing to answer and
          nowhere to go back to — it resolves itself and the finish opens — so this says what
          is happening and offers no control at all. `base`, because it is neither a warning
          nor an explanation of the product: it is a state that is passing. */}
      {commit.kind === 'uploading' ? (
        <Note variant="base" title={UPLOADING_TITLE}>
          {UPLOADING_BODY}
        </Note>
      ) : null}

      <Button
        label={FINISH_LABEL}
        size="lg"
        // Closed until the part is complete, and both halves of that are `readyToCommit`
        // reporting — this step's own question and every answer behind it.
        disabled={!open}
        // Blocked while the request is in flight, which is the courtesy. The defence is the
        // idempotency key: it belongs to the part rather than to the press, so a second tap
        // that beats this state is the same commit rather than a second one.
        busy={commit.kind === 'committing'}
        busyLabel={FINISHING_WORD}
        onPress={() => finish(() => router.replace(AFTER_THE_STEPS))}
        accessibilityHint={finishHint(commit.kind, wanted?.copy.finishHint, unansweredHint)}
      />
    </>
  );
}
