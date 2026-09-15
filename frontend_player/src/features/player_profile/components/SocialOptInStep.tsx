/**
 * Step eight of onboarding's second part: **may we suggest games?**
 *
 * The last of the eight, and the only one that collects **consent**. Everything else the part
 * asks for is a preference — a preference can be wrong, corrected, or left blank, and none
 * of those is a moral event. This one is a record of what a person agreed to, which is why
 * it is the step with the frozen copy, the pinned version identifier and no third control.
 *
 * ## The two answers are buttons
 *
 * They were chips, and a chip is a **filter** over content the player can already see (6.2).
 * These are the two answers to the screen's only question and the one press that opens the
 * finish, so they are the size of an answer: stacked, full width, the given one filled and
 * the other outlined. Neither is `primary` — coral is the one accent (1.2) and the finish
 * has it — and `accessibilityState.selected` is announced by both, because *not chosen* and
 * *not a choice* are different things to be told.
 *
 * **No wording changed with the control**, which is why that alone did not bump the copy
 * version. Two rewordings have: `v2` dropped the line under the title, and `v3` rewrote two
 * of the three promises and the scope note. See `optInPresentation`, where both are retired
 * and retained.
 *
 * ## Never pre-answered, and no way past it that is not an answer
 *
 * Neither control is selected on arrival, and the finish is closed until one of them is.
 * There is **no skip, dismiss, close or decide-later anywhere on this screen** — a player
 * who left through one would be neither opted in nor opted out, and the guess somebody
 * downstream would then have to make is exactly what consent exists to remove
 * (`CONTEXT.md` — *Skipping is not consent*).
 *
 * **No is a complete answer.** Both controls open the finish, because a player who declines
 * has finished this step as completely as one who accepts; a gate that opened only on yes
 * would be the product withholding the rest of itself until it got the answer it wanted.
 *
 * ## The words are the record, so they are not this file's
 *
 * `optInPresentation` owns every sentence and the version identifier stamped beside the
 * answer, because re-wording a consent card is a new version with the old one retained
 * rather than an edit. What is left here is what a player sees and touches.
 *
 * The card promises only what this answer governs. **Opting out stops the engine pushing,
 * not the player existing** — search and matchmaking are unaffected either way — and the
 * scope note is the sentence that says so. It is not decoration: without it the card reads
 * as *disappear or be suggested to*, which is a choice nobody is being offered.
 *
 * **That note is now the first thing on the screen**, above the card rather than under it.
 * The card is titled *If you say yes* and every line in it is conditional on that answer, so
 * a player leaning towards no used to read three promises addressed to somebody else before
 * reaching the one sentence addressed to them. It is `v3` copy in `v3`'s position, and the
 * two changed together.
 *
 * ## This is where the part is written, and it is the only place that is
 *
 * The answer and its copy version go into the client-held draft like the seven before it, and
 * then the finish sends **the whole of it in one request**
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)). Not eight
 * writes: a partial commit — the tags saved and the consent lost — is the worst outcome this
 * part has available to it.
 *
 * What that costs this screen is two states it is the only one that can have. **A commit
 * that did not land** leaves the player exactly here, with the draft intact and the control
 * that failed as the retry, and nothing anywhere claiming the account was set up. **A commit
 * with an answer still missing** cannot be sent at all, and the one it is realistically
 * short of is the area — the location step names that cost when a player passes it, and this
 * is where it is collected, with the way back one press away.
 *
 * There is a third, and it is the seam between the two: **a failure whose code names a
 * step.** The commit re-validates every rule a picker enforced, so `availability_grid_empty`
 * can arrive from a build that predates the week's floor or from a replayed request — and
 * *try again* is then the one sentence that is not true, because the identical body fails
 * identically. It is drawn as the failure it is, in the words of the answer it names, with
 * the same control back to the step that takes it. `intro_not_admitted` is the other code
 * that names a step, and the one this screen will actually meet: the fence on the line is
 * the server's pattern, so a phone number typed on step two is refused here, six screens
 * later, in the sentence its reason names and with *Change your intro* under it
 * (ADR-0170 §2). The finish stays pressable, exactly as it does after any other correctable
 * refusal; what changes is that the screen no longer promises that pressing it is enough.
 *
 * The sequencing is `useCommitProfile`'s and the rule about what a complete part is is
 * `readyToCommit`'s. What is left here is what a player sees and touches.
 */

import { useRouter } from 'expo-router';
import { Fragment } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { recoveryMessage } from '@/shared/errors';
import { Button, Card, Hairline, Note, theme } from '@/shared/ui';

import { mayFinish, type CommitStanding } from '../domain/profileCommit';
import { optInStanding } from '../domain/proposalsOptIn';
import { useCommitProfile } from '../hooks/useCommitProfile';
import { useProfileDraft } from '../store/profileDraft.store';

import {
  COMMIT_FAILED_BODY,
  COMMIT_FAILED_TITLE,
  FINISHING_WORD,
  FINISH_HINT,
  UPLOADING_BODY,
  UPLOADING_HINT,
  UPLOADING_TITLE,
  answerStillWanted,
  stepTheCommitRefused,
} from './commitPresentation';
import { SOCIAL_STEP_PATH, pathThatAsks } from './socialStepRoutes';
import {
  OPT_IN_ANSWERS,
  OPT_IN_EYEBROW,
  OPT_IN_FINISH_BLOCKED_HINT,
  OPT_IN_FINISH_LABEL,
  OPT_IN_NEVER_PRE_TICKED,
  OPT_IN_PROMISES,
  OPT_IN_PROMISE_HEADING,
  OPT_IN_SCOPE,
  PROPOSALS_OPT_IN_COPY_VERSION,
} from './optInPresentation';
import { SocialStepLayout } from './SocialStepLayout';

/**
 * Where the part leads once the server has it: what Raketa keeps, and then the app.
 *
 * **Not the ratings summary — the player has already seen it.** It is the screen the second
 * part is now entered *from*, so landing back on it after the commit would show a player the
 * same account of the same walk twice, with the second one following seven questions that had
 * nothing to do with it.
 *
 * A route literal rather than an import, and that is the boundary working. What follows the
 * commit is onboarding's, and this feature owns the profile rather than the flow that
 * collects it. Written here, beside the one press that goes there, rather than in
 * `socialStepRoutes`: that table is the eight steps, and the eight steps stop before this.
 */
const AFTER_THE_PART = '/data';

/**
 * Why the finish will not move, for whoever cannot see that it will not.
 *
 * Three closed reasons and they are genuinely different: an answer one of the seven earlier
 * steps asks for, a photo still arriving, and the question on this very screen. Only the
 * last is `optInPresentation`'s — reaching for *choose yes or no above to finish* in either
 * of the other two would tell a player to do something they have already done.
 */
function finishHint(standing: CommitStanding['kind'], stepHint: string | undefined): string {
  if (standing === 'uploading') return UPLOADING_HINT;
  if (standing !== 'incomplete') return FINISH_HINT;
  return stepHint ?? OPT_IN_FINISH_BLOCKED_HINT;
}

export function SocialOptInStep() {
  const router = useRouter();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);
  const { standing: commit, finish } = useCommitProfile();

  const standing = optInStanding(draft?.proposalsOptIn);

  /**
   * Record the answer **with the words it was given against**, always together.
   *
   * The version is stamped here rather than in the domain because *which wording was
   * shown* is this screen's fact and nobody else's — the file that drew the sentences is
   * the only one that can honestly name them. What the domain guarantees is the other
   * half: `ProposalsOptIn.copyVersion` is required, so an answer with no wording beside it
   * is not a value that can be built at all.
   *
   * The last press wins, plainly: `recordAnswer` replaces the field, so changing your mind
   * before finishing costs nothing and leaves the other answers alone. Every press
   * writes, including a press on the control already selected — re-affirming an answer is
   * itself a fact about consent, and the step is not the place to decide it is not worth
   * recording.
   */
  const say = (accepted: boolean) =>
    answer({ proposalsOptIn: { accepted, copyVersion: PROPOSALS_OPT_IN_COPY_VERSION } });

  /**
   * What the finish is waiting for, if anything.
   *
   * `mayFinish` is not consulted separately any more, and that is not a rule being dropped:
   * *an answer that has not been given is not an answer* is one of the three the readiness
   * rule reports, so the finish still opens on either answer and on neither absence. What
   * changed is that the same control now also refuses a part that is short of an area,
   * which no rule about consent could ever have said.
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
    <SocialStepLayout
      step="opt-in"
      // The position line gives way to the copy's own: *before finishing* already says
      // where the player is, and what this line has to carry is that one question is the
      // whole of what is left.
      eyebrow={OPT_IN_EYEBROW}
      action={
        <>
          {/* The failure, and it is `coral` and an alert because it is a status about
              something the player just did rather than an explanation of the product. It
              says what did not happen and that nothing was lost — never that setting up
              worked, which is the one claim a failed commit must not make. */}
          {commit.kind === 'failed' ? (
            <Note variant="coral" title={COMMIT_FAILED_TITLE} accessibilityRole="alert">
              {/* A refusal that names an answer says so instead of `recoveryMessage`'s
                  category sentence and the promise that pressing again is enough. Both
                  would be untrue here: the same body fails the same way, and the thing that
                  fixes it is a step behind this one. Nothing was lost either way. */}
              {refused === undefined
                ? `${recoveryMessage(commit.error)} ${COMMIT_FAILED_BODY}`
                : refused.body}
            </Note>
          ) : null}

          {/* An answer the commit cannot do without, and the way back to the step that asks
              it. `amber` rather than `coral`: nothing has gone wrong and nothing is lost —
              this is a step still to be taken, and it is one press away. */}
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

          {/* The way back, for a refusal. The coral note above already carries the words —
              a second one under it would say the same thing twice — so what is left is the
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
              nowhere to go back to — it resolves itself and the finish opens — so this says
              what is happening and offers no control at all. `base`, because it is neither a
              warning nor an explanation of the product: it is a state that is passing. */}
          {commit.kind === 'uploading' ? (
            <Note variant="base" title={UPLOADING_TITLE}>
              {UPLOADING_BODY}
            </Note>
          ) : null}

          <Button
            label={OPT_IN_FINISH_LABEL}
            size="lg"
            // Closed until answered, open on either answer — and closed again for a part
            // that is short of something the eight steps must carry. Both are `readyToCommit`
            // reporting, so *no* can never be mistaken for *not yet*.
            disabled={!open}
            // Blocked while the request is in flight, which is the courtesy. The defence is
            // the idempotency key: it belongs to the part rather than to the press, so a
            // second tap that beats this state is the same commit rather than a second one.
            busy={commit.kind === 'committing'}
            busyLabel={FINISHING_WORD}
            onPress={() => finish(() => router.replace(AFTER_THE_PART))}
            accessibilityHint={finishHint(commit.kind, wanted?.copy.finishHint)}
          />
        </>
      }
    >
      {/* First on the screen, above the card rather than below it.

          `info`, because it explains what the product does rather than reporting a status
          about the player's own answer (design-system 1.3). It moved to the top because the
          card under it is titled *If you say yes* and is conditional on one of the two
          answers — so a player who is not going to give that answer read three promises that
          were not addressed to them before reaching the one sentence that was. This is what
          makes *no* a decision about proposals rather than a decision about being seen at
          all, and it belongs before the question, not after it. */}
      <Note variant="info">{OPT_IN_SCOPE}</Note>

      <Card>
        <Text style={s.heading}>{OPT_IN_PROMISE_HEADING}</Text>

        {/* **Stacked, not `Row`.** 5.5 is the key-value *line* — label left, value right,
            `space-between` — and it is right for the figures and evidence rows it names.
            Here the value is a whole sentence, and a sentence pushed into the right half of
            a phone-width row is four words a line. So the term sits above what it promises,
            and only 5.5's divider rule is borrowed. */}
        <View style={s.promises}>
          {OPT_IN_PROMISES.map((promise, index) => {
            // One accessibility element, not two: *You may receive* and the sentence
            // completing it mean nothing read a screen apart — which is the obligation 5.5
            // states for its own rows, and it does not depend on the layout.
            const promised = (
              <View accessible accessibilityLabel={`${promise.term} ${promise.detail}`}>
                <Text style={s.term}>{promise.term}</Text>
                <Text style={s.detail}>{promise.detail}</Text>
              </View>
            );

            // The divider is drawn from the second promise onward, so the first has no rule
            // above it and the last none below it — 5.5's `index > 0`, expressed with the
            // primitive that owns the fold. **No gap on this container**: `Hairline` already
            // sets the space on both sides of the line, and a gap stacked on top of it would
            // put the rule closer to the promise below than the one above.
            return index === 0 ? (
              <Fragment key={promise.term}>{promised}</Fragment>
            ) : (
              <Hairline key={promise.term}>{promised}</Hairline>
            );
          })}
        </View>
      </Card>

      {/* Immediately above the two controls, because it is a claim about them: neither is
          selected, and nothing else the player has done was read as answering this. */}
      <Text style={s.smallPrint}>{OPT_IN_NEVER_PRE_TICKED}</Text>

      {/* The order is the copy's, not this screen's — No first, because the option a screen
          puts first is the one it reads as recommending.

          **Buttons, and full width.** These were chips, and a chip is a filter over content
          the player can already see (6.2) — a row of two pills reads as *narrow this down*.
          These are the two answers to the only question on the screen, so they are the size
          of an answer. Neither is `primary`: coral is the one accent (1.2) and the finish
          below has it, so the answer that has been given is `dark` and the other is
          `secondary` — a luminance inversion, the same thing the chip's ink fill was doing.
          `selected` carries the same fact for whoever sees neither, and it is announced by
          both controls rather than only by the chosen one. */}
      <View style={s.answers}>
        {OPT_IN_ANSWERS.map(({ accepted, label }) => {
          const chosen = standing.kind === 'answered' && standing.accepted === accepted;

          return (
            <Button
              key={label}
              label={label}
              size="lg"
              variant={chosen ? 'dark' : 'secondary'}
              selected={chosen}
              onPress={() => say(accepted)}
            />
          );
        })}
      </View>
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  // The card carries no gap of its own: `Hairline` owns the space around each fold, and
  // this is the one step between the heading and the first promise, which has no fold.
  promises: { marginTop: theme.space.xs },
  heading: { ...theme.type.cardTitle, color: theme.color.ink },
  term: { ...theme.type.inlineTitle, color: theme.color.ink },
  // `ink`, not `muted`: this is the substance of what is being agreed to, and the muted
  // role is for text that is genuinely secondary to something else on the screen.
  detail: { ...theme.type.tiny, color: theme.color.ink },
  smallPrint: { ...theme.type.tiny, color: theme.color.muted },
  // Stacked, not a row: both labels are a sentence naming what they do, and two of those
  // side by side on a phone are two clipped words. The gap is the one between stacked
  // controls in an action group.
  answers: { gap: theme.space.sm },
});
