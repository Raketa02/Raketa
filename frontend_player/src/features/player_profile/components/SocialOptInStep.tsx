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
 * ## Nothing here reaches the network
 *
 * The answer and its copy version go into the part's client-held draft like the five before
 * it, and the whole of it is sent in one commit at the end of the part
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)). That
 * commit is not built yet, which is what the note above the finish says out loud rather
 * than navigating somewhere that would claim the account was set up.
 */

import { Fragment } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, Chip, Hairline, Note, theme } from '@/shared/ui';

import { mayFinish, optInStanding } from '../domain/proposalsOptIn';
import { useProfileDraft } from '../store/profileDraft.store';

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
 * What finishing does is the profile commit, and a commit is not a screen — it arrives with
 * its own ticket, together with the idempotency key that makes a double tap produce one
 * profile. The control is here now because **the rule this step owns is about the control**:
 * when it opens, and on what. Where it leads is the next ticket's.
 */
const finishNotBuiltYet = () => undefined;

export function SocialOptInStep() {
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

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

  const open = mayFinish(standing);

  return (
    <SocialStepLayout
      step="opt-in"
      // The position line gives way to the copy's own: *before finishing* already says
      // where the player is, and what this line has to carry is that one question is the
      // whole of what is left.
      eyebrow={OPT_IN_EYEBROW}
      action={
        <>
          {/* `base` rather than `info`: this is not an explanation of the product, it is a
              statement about the state of the build — the one thing on this screen that
              will be deleted rather than re-worded. */}
          <Note variant="base">
            This is the last of the six. Finishing sends everything at once — that step is still to
            come.
          </Note>

          <Button
            label={OPT_IN_FINISH_LABEL}
            size="lg"
            // The whole of this step's rule, in one prop: closed until answered, open on
            // either answer. `mayFinish` is where that is decided, so *no* can never be
            // mistaken for *not yet*.
            disabled={!open}
            onPress={finishNotBuiltYet}
            // Only while it is closed. An enabled control that repeated its own label as a
            // hint would be read twice, and there is nothing to promise about what
            // finishing sends until there is a commit to send it.
            accessibilityHint={open ? undefined : OPT_IN_FINISH_BLOCKED_HINT}
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
