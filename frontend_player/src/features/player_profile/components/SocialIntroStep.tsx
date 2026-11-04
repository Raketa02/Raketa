/**
 * Step two of onboarding's second part: **say it in your own words.**
 *
 * One box, a counter to 250, and two ways forward: *Next* with the line, or *Skip* with
 * nothing. It is the first free text this platform shows a stranger
 * ([ADR-0170](../../../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md);
 * the cap from [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §9),
 * and the whole of the moderation story is a rule at the write — a line carrying a way to
 * reach somebody is refused by the server, with the reason and never the pattern — so what
 * this screen owes the player is to make the two shape refusals impossible to walk past. The
 * third is said only to a line that breaks it, at the commit: the paragraph that announced it
 * under the box went with ADR-0200 §9.
 *
 * ## Nothing here decides anything, and the box is not here either
 *
 * The cap, the count, the line-break rule and what the commit carries are `intro`'s, with
 * their own tests and no renderer; the sentences are `introPresentation`'s; the box with its
 * counter and hint — and the cap drawn as a refusal rather than as a `maxLength` — is
 * `IntroField`, which the You tab's *Intro* draws too
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §6 — the day ADR-0170 §5 named). What is left here is the step's own: its chrome, *Next*
 * and *Skip*.
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

import { Button } from '@/shared/ui';

import { introStanding } from '../domain/intro';
import { stepAfter } from '../domain/socialSteps';
import { useProfileDraft } from '../store/profileDraft.store';

import { IntroField } from './IntroField';
import {
  INTRO_NEXT_LABEL,
  INTRO_REFUSAL_SENTENCE,
  INTRO_SKIP_LABEL,
  introNextHint,
  introSkipHint,
} from './introPresentation';
import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';

export function SocialIntroStep() {
  const router = useRouter();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('intro');
  const written = draft?.intro ?? '';
  const standing = introStanding(written);
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
      <IntroField
        written={written}
        onChangeText={(text) => answer({ intro: text })}
        refusal={refusal}
      />
    </SocialStepLayout>
  );
}
