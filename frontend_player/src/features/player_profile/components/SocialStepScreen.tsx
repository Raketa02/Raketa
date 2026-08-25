/**
 * One step of onboarding's second part — as a **placeholder**.
 *
 * This is the tracer bullet, not the step. The part's route sequence, its chrome, its
 * client-held draft, its back and forward, and the entry gate that lands a player here all
 * work end to end; what each screen actually *asks* arrives with the ticket that builds it.
 * The whole point of landing it in this order is that six steps get filled into a flow that
 * already walks, rather than six flows getting invented one screen at a time.
 *
 * ## What is permanent here
 *
 * The chrome and the two moves. **The back control is absent on the first step**, and that
 * is `stepBefore` answering rather than a prop this screen remembers to leave off — behind
 * step one is a rated Assessment, and an answer is revisable for as long as its run is and
 * no longer. **Both moves `replace`**, so the part is a flat sequence of six screens with no
 * stack behind it: back can only ever reach the previous step, never the result or the
 * review, because there is no history entry holding one. Leaving the part by the system's
 * own back gesture restarts it at step one, which is exactly what
 * [ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md) says leaving
 * mid-part does.
 *
 * **Nothing here reaches the network**, in either direction and on any step. The commit at
 * the end of the part is the only write the part makes, and it is not built yet.
 */

import { useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, Chip, Note, ScreenHeader, theme } from '@/shared/ui';

import type { ProfileDraft } from '../domain/ProfileDraft';
import { stepAfter, stepBefore, type SocialStep } from '../domain/socialSteps';
import { useProfileDraft } from '../store/profileDraft.store';

import { stepCopy, stepEyebrow } from './socialStepPresentation';

/**
 * Each step's route, as a literal the router's typed hrefs accept.
 *
 * The step names *are* the route segments, so this table is one-to-one by construction — it
 * exists because a template literal is not a typed href, not because there is a second
 * naming scheme to translate between.
 */
const PATH = {
  tags: '/tags',
  photos: '/photos',
  availability: '/availability',
  location: '/location',
  radius: '/radius',
  'opt-in': '/opt-in',
} as const satisfies Record<SocialStep, string>;

/**
 * The placeholder answer each step records, and how to tell it has.
 *
 * **This is scaffolding and it is meant to look like scaffolding.** A step with no control
 * cannot answer anything, and a draft nothing can write to cannot be shown to survive a walk
 * through the part — which is the one property this ticket exists to prove. So each
 * placeholder writes one obviously fake value into its own slot and touches nothing else.
 * Nothing is sent to the server anywhere in this ticket, so an illegal value costs nothing;
 * a *plausible* one would be worse, because the ticket that builds the step would have no
 * reason to notice it was still there.
 *
 * Each step's ticket deletes its row here along with the placeholder body it replaces.
 */
const PLACEHOLDER: Readonly<
  Record<
    SocialStep,
    { readonly answer: Partial<ProfileDraft>; readonly held: (draft: ProfileDraft) => boolean }
  >
> = {
  tags: {
    answer: { socialTagIds: ['PLACEHOLDER_TAG'] },
    held: (draft) => draft.socialTagIds.length > 0,
  },
  photos: {
    answer: { photoIds: ['placeholder-photo'] },
    held: (draft) => draft.photoIds.length > 0,
  },
  availability: {
    answer: { availability: [{ day: 1, part: 'morning' }] },
    held: (draft) => draft.availability.length > 0,
  },
  location: {
    answer: { location: { latitude: 0, longitude: 0 } },
    held: (draft) => draft.location !== undefined,
  },
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
  readonly step: SocialStep;
}

export function SocialStepScreen({ step }: SocialStepScreenProps) {
  const router = useRouter();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

  const { title, asks } = stepCopy(step);
  const previous = stepBefore(step);
  const next = stepAfter(step);
  const answered = draft !== undefined && PLACEHOLDER[step].held(draft);

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <ScreenHeader
        eyebrow={stepEyebrow(step)}
        title={title}
        // Absent on the first step, because there is no step before it — the rule, not a
        // decision taken here.
        onBack={previous === undefined ? undefined : () => router.replace(PATH[previous])}
        backLabel={previous === undefined ? undefined : `Back to ${stepCopy(previous).title}`}
      />

      <ScrollView contentContainerStyle={s.content}>
        <Card style={s.card}>
          <Text style={s.cardTitle}>{asks}</Text>
          <Text style={s.body}>
            Nothing you answer here is sent anywhere until the end of these six steps, and you can
            go back and change any of it.
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
      </ScrollView>

      <View style={s.action}>
        {next === undefined ? (
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
            onPress={() => router.replace(PATH[next])}
            accessibilityHint={`Goes to ${stepCopy(next).title}`}
          />
        )}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  card: { gap: theme.space.xxs },
  cardTitle: { ...theme.type.cardTitle, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.muted },
  placeholderControl: { alignItems: 'flex-start' },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
  },
});
