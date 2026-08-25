/**
 * Step six of onboarding's second part: **may we suggest games?**
 *
 * The last of the six, and the only one that collects **consent**. Everything else the part
 * asks for is a preference — a preference can be wrong, corrected, or left blank, and none
 * of those is a moral event. This one is a record of what a person agreed to, which is why
 * it is the step with the frozen copy, the pinned version identifier and no third control.
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
 * ## This is where the part is written, and it is the only place that is
 *
 * The answer and its copy version go into the client-held draft like the five before it, and
 * then the finish sends **the whole of it in one request**
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)). Not six
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
 * The sequencing is `useCommitProfile`'s and the rule about what a complete part is is
 * `readyToCommit`'s. What is left here is what a player sees and touches.
 */

import { useRouter } from 'expo-router';
import { Fragment } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { recoveryMessage } from '@/shared/errors';
import { Button, Card, Chip, Hairline, Note, theme } from '@/shared/ui';

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
} from './commitPresentation';
import { pathThatAsks } from './socialStepRoutes';
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
import { stepCopy } from './socialStepPresentation';

/**
 * Where the part leads once the server has it: the closing screens, then the app.
 *
 * A route literal rather than an import, and that is the boundary working. What follows the
 * commit is onboarding's — the summary of the ratings this walk produced, and what Raketa
 * keeps — and this feature owns the profile rather than the flow that collects it. Written
 * here, beside the one press that goes there, rather than in `socialStepRoutes`: that table
 * is the six steps, and the six steps stop before this.
 */
const AFTER_THE_PART = '/done';

/**
 * Why the finish will not move, for whoever cannot see that it will not.
 *
 * Three closed reasons and they are genuinely different: an answer one of the five earlier
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
   * before finishing costs nothing and leaves the other five answers alone. Every press
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
              {`${recoveryMessage(commit.error)} ${COMMIT_FAILED_BODY}`}
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
            // that is short of something the six steps must carry. Both are `readyToCommit`
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
      <Text style={s.asks}>{stepCopy('opt-in').asks}</Text>

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

      {/* The correction, and it is `info` because it explains what the product does rather
          than reporting a status about the player's own answer (design-system 1.3). It sits
          between the promises and the controls because it is what makes *no* a decision
          about proposals rather than a decision about being seen at all. */}
      <Note variant="info">{OPT_IN_SCOPE}</Note>

      {/* Immediately above the two controls, because it is a claim about them: neither is
          selected, and nothing else the player has done was read as answering this. */}
      <Text style={s.smallPrint}>{OPT_IN_NEVER_PRE_TICKED}</Text>

      {/* The order is the copy's, not this screen's — No first, because the option a screen
          puts first is the one it reads as recommending. */}
      <View style={s.answers}>
        {OPT_IN_ANSWERS.map(({ accepted, label }) => (
          <Chip
            key={label}
            label={label}
            // Selection is the chip's ink fill — a luminance inversion rather than a change
            // of hue — **and** `accessibilityState.selected`, which the chip always
            // announces, selected or not. Neither half is the whole fact.
            selected={standing.kind === 'answered' && standing.accepted === accepted}
            onPress={() => say(accepted)}
          />
        ))}
      </View>
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  /** Secondary text is always `tiny` in `muted` — what this step asks. */
  asks: { ...theme.type.tiny, color: theme.color.muted },
  // The card carries no gap of its own: `Hairline` owns the space around each fold, and
  // this is the one step between the heading and the first promise, which has no fold.
  promises: { marginTop: theme.space.xs },
  heading: { ...theme.type.cardTitle, color: theme.color.ink },
  term: { ...theme.type.inlineTitle, color: theme.color.ink },
  // `ink`, not `muted`: this is the substance of what is being agreed to, and the muted
  // role is for text that is genuinely secondary to something else on the screen.
  detail: { ...theme.type.tiny, color: theme.color.ink },
  smallPrint: { ...theme.type.tiny, color: theme.color.muted },
  // Wrapping rather than a fixed row: both labels name what they do, so at a large OS text
  // size they become two full-width lines rather than two clipped words.
  answers: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});
