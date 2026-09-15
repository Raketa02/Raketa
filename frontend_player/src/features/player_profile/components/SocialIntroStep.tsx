/**
 * Step two of onboarding's second part: **say it in your own words.**
 *
 * One box, a counter to a hundred, a line of small print, and two ways forward: *Next* with
 * the line, or *Skip* with nothing. It is the first free text this platform shows a stranger
 * ([ADR-0170](../../../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)),
 * and the whole of the moderation story is a rule at the write — a line carrying a way to
 * reach somebody is refused by the server, with the reason and never the pattern — so what
 * this screen owes the player is to make the two shape refusals impossible to walk past and
 * to say the third one before it is met.
 *
 * ## Nothing here decides anything
 *
 * The cap, the count, the line-break rule and what the commit carries are `intro`'s, with
 * their own tests and no renderer; the sentences are `introPresentation`'s. What is left
 * here is what a player sees — the same split every step before it made, and for the same
 * reason: the profile editor will obey these rules from a screen that looks nothing like
 * this one, on the day the intro becomes editable with the tags and the photo (ADR-0170 §5).
 *
 * ## The cap is drawn as a refusal rather than as a `maxLength`
 *
 * `WhereField`'s argument, one feature over, and it holds here: a `maxLength` swallows the
 * tail of a paste, and a shortened line is one the person who typed it believes they wrote
 * whole — in front of every stranger who reads it. So the box takes everything, the counter
 * keeps counting past a hundred, the sentence under the box says what is wrong, and *Next*
 * stays shut until it is not. The box grows to a few lines so a hundred characters can be
 * read back whole, and the return key **dismisses the keyboard rather than breaking the
 * line** — a line break is the second shape refusal, and the ordinary way of producing one
 * should not produce it. A pasted one still can, and is refused under the box the same way.
 *
 * ## Skip is visible, and it clears
 *
 * The step is optional, and a player learns that by reading the screen rather than by
 * finding *Next* open on an empty box. Skip carries nothing forward **whatever is in the
 * box**: a skip that sent what happened to be typed would be the one thing the word does not
 * say, and walking back after one finds the box empty, which is what was skipped.
 *
 * ## The line lives in the draft, not in this screen
 *
 * Every keystroke writes through to the part's client-held draft, as typed, so walking to
 * step three and back finds the line exactly as it was left. Nothing is sent anywhere: the
 * draft is in memory until the one commit at the end of the part
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)), and the
 * commit carries the line trimmed or not at all.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { Button, TextField, theme } from '@/shared/ui';

import { introLength, introStanding } from '../domain/intro';
import { stepAfter } from '../domain/socialSteps';
import { useProfileDraft } from '../store/profileDraft.store';

import {
  INTRO_FIELD_HINT,
  INTRO_FIELD_LABEL,
  INTRO_NEXT_LABEL,
  INTRO_PLACEHOLDER,
  INTRO_REFUSAL_SENTENCE,
  INTRO_RULE,
  INTRO_SKIP_LABEL,
  introCounter,
  introNextHint,
  introSkipHint,
  spokenIntroCounter,
} from './introPresentation';
import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';

/**
 * How many lines the box may grow to before it scrolls.
 *
 * A hundred characters is two lines on the deck card at the mock's size and three in this
 * box at the value role, so three is where a line at the cap can be read back whole. One
 * more than that is room for the overrun the counter is there to show.
 */
const INTRO_LINES = 4;

export function SocialIntroStep() {
  const router = useRouter();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('intro');
  const written = draft?.intro ?? '';
  const standing = introStanding(written);
  // The count is of the line as the cap reads it — trimmed — and not of the box: the spaces
  // around a line are not part of it, and a counter that said `104 / 100` beside an open
  // *Next* would be arguing with the rule it is there to show.
  const length = introLength(written.trim());
  const refusal = standing.kind === 'refused' ? INTRO_REFUSAL_SENTENCE[standing.reason] : undefined;

  const goOn = () => {
    if (next !== undefined) router.replace(SOCIAL_STEP_PATH[next]);
  };

  return (
    <SocialStepLayout
      step="intro"
      action={
        next === undefined ? null : (
          <>
            <Button
              label={INTRO_NEXT_LABEL}
              size="lg"
              // Shut on a line the server would refuse on shape, and on nothing else: an
              // empty box is an answer, and Next carries it as none exactly as Skip does.
              disabled={refusal !== undefined}
              onPress={goOn}
              // A blocked control names what is wrong rather than merely being grey.
              accessibilityHint={refusal ?? introNextHint(stepCopy(next).title)}
            />
            <Button
              label={INTRO_SKIP_LABEL}
              variant="secondary"
              size="lg"
              onPress={() => {
                // Cleared, not merely left: *skip* means *no intro*, whatever was typed.
                answer({ intro: '' });
                goOn();
              }}
              accessibilityHint={introSkipHint(stepCopy(next).title)}
            />
          </>
        )
      }
    >
      <TextField
        label={INTRO_FIELD_LABEL}
        placeholder={INTRO_PLACEHOLDER}
        value={written}
        onChangeText={(text) => answer({ intro: text })}
        growTo={INTRO_LINES}
        // Return dismisses the keyboard. A line break is a refusal, and the key that would
        // ordinarily insert one should not be the key that produces it.
        submitBehavior="blurAndSubmit"
        // Prose a person writes, not an identifier: the platform's own correction and
        // capitalisation stay on, and there is nothing on a phone's saved-values list that
        // is a sentence about somebody.
        autoComplete="off"
        accessibilityHint={INTRO_FIELD_HINT}
        {...(refusal === undefined ? {} : { error: refusal })}
      />

      {/* Right-aligned under the box, in the number role — every figure is mono and
          tabular, which is what keeps `9 / 100` and `10 / 100` from shifting the line. Spoken
          as a count rather than as a fraction, because `/` is not a word. */}
      <Text style={s.counter} accessibilityLabel={spokenIntroCounter(length)}>
        {introCounter(length)}
      </Text>

      {/* The rule, once, before the refusal that enforces it is six screens away. */}
      <View style={s.rule}>
        <Text style={s.smallPrint}>{INTRO_RULE}</Text>
      </View>
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  counter: {
    ...theme.num.xs,
    ...theme.tabular,
    color: theme.color.muted,
    textAlign: 'right',
  },
  rule: { paddingTop: theme.space.xs },
  smallPrint: { ...theme.type.tiny, color: theme.color.muted },
});
