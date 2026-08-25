/**
 * A step of onboarding's second part that has **not been built yet** — as a placeholder.
 *
 * This is what is left of the tracer bullet. The part's route sequence, its chrome, its
 * client-held draft, its back and forward, and the entry gate that lands a player here all
 * work end to end; what each screen actually *asks* arrives with the ticket that builds it,
 * and four of them have landed — the Social tags step, the photos step, the availability step
 * and the location step are real screens now and no longer pass through here.
 *
 * The chrome and the back control moved to `SocialStepLayout`, which every step wears,
 * built or not. What stays here is only the standing-in: a control that records something
 * obviously fake, and a forward that goes to the next step.
 *
 * **Nothing here reaches the network**, in either direction and on any step.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, Chip, Note, theme } from '@/shared/ui';

import type { ProfileDraft } from '../domain/ProfileDraft';
import { stepAfter, type SocialStep } from '../domain/socialSteps';
import { useProfileDraft } from '../store/profileDraft.store';

import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';

/**
 * The steps still standing in for themselves.
 *
 * A closed union rather than every step, so a ticket that builds one and forgets to take it
 * out of the table below fails `pnpm typecheck` instead of leaving a screen that quietly
 * offers both its real control and a placeholder.
 */
export type UnbuiltSocialStep = Exclude<
  SocialStep,
  'tags' | 'photos' | 'availability' | 'location'
>;

/**
 * The placeholder answer each step records, and how to tell it has.
 *
 * **This is scaffolding and it is meant to look like scaffolding.** A step with no control
 * cannot answer anything, and a draft nothing can write to cannot be shown to survive a walk
 * through the part. So each placeholder writes one obviously fake value into its own slot and
 * touches nothing else. Nothing is sent to the server anywhere in the part yet, so an illegal
 * value costs nothing; a *plausible* one would be worse, because the ticket that builds the
 * step would have no reason to notice it was still there.
 *
 * Each step's ticket deletes its row here along with the placeholder body it replaces.
 */
const PLACEHOLDER: Readonly<
  Record<
    UnbuiltSocialStep,
    { readonly answer: Partial<ProfileDraft>; readonly held: (draft: ProfileDraft) => boolean }
  >
> = {
  radius: {
    answer: { searchRadiusKm: 0 },
    held: (draft) => draft.searchRadiusKm !== undefined,
  },
  'opt-in': {
    // `false`, never `true`. The opt-in is the one field the product says is never
    // pre-answered, and a placeholder that encodes a *yes* is the one placeholder that
    // could survive into something that matters. Absent is still what unanswered means —
    // what is being stood in for here is *an answer having been given*, not consent.
    answer: { proposalsOptIn: { accepted: false, copyVersion: 'placeholder' } },
    held: (draft) => draft.proposalsOptIn !== undefined,
  },
};

export interface SocialStepScreenProps {
  readonly step: UnbuiltSocialStep;
}

export function SocialStepScreen({ step }: SocialStepScreenProps) {
  const router = useRouter();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

  const next = stepAfter(step);
  const answered = draft !== undefined && PLACEHOLDER[step].held(draft);

  return (
    <SocialStepLayout
      step={step}
      action={
        next === undefined ? (
          // The last step's forward is the profile commit, and a commit is not a screen.
          // Until it exists this part ends here rather than navigating somewhere that would
          // claim the account was set up.
          <Note variant="base">
            This is the last of the six. Finishing sends everything at once — that step is still to
            come.
          </Note>
        ) : (
          <Button
            label="Continue"
            size="lg"
            onPress={() => router.replace(SOCIAL_STEP_PATH[next])}
            accessibilityHint={`Goes to ${stepCopy(next).title}`}
          />
        )
      }
    >
      <Card style={s.card}>
        <Text style={s.cardTitle}>{stepCopy(step).asks}</Text>
        <Text style={s.body}>
          Nothing you answer here is sent anywhere until the end of these six steps, and you can go
          back and change any of it.
        </Text>
      </Card>

      {/* `info` rather than `amber`: this explains what the screen is, and amber means
          *watch this, reversible, not yet wrong* — a status about the player's answer
          rather than an explanation of the app (design-system 1.3). */}
      <Note variant="info" title="This step is not built yet">
        The screen that asks this is on its way. What works today is the walk itself — forward,
        back, and every answer still where you left it.
      </Note>

      <View style={s.placeholderControl}>
        <Chip
          label={answered ? 'Answered' : 'Answer this step'}
          selected={answered}
          onPress={() => answer(PLACEHOLDER[step].answer)}
          accessibilityHint="Stands in for this step's real control until it is built"
        />
      </View>
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.xxs },
  cardTitle: { ...theme.type.cardTitle, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.muted },
  placeholderControl: { alignItems: 'flex-start' },
});
