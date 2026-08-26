/**
 * Which sports do you play?
 *
 * Multi-select, one card per sport carrying its identity colour. **The selection is never
 * persisted** — not to the server, not to the device. It exists only to order the next few
 * assessments, and a sport left unselected today can be rated any time later.
 *
 * Each sport is rated independently and levels are never borrowed between them. **The screen
 * no longer says so** — the picker is a list of sports and a control, and the rule shows up
 * where it can be seen rather than asserted: one result screen per sport, each with its own
 * evidence.
 *
 * Continuing starts the first selected sport's assessment and lands on its opening
 * question. It is `replace`, not `push`: a player walks back through the questionnaire
 * with its own control (ADR-0020), and the system back gesture must not be a second,
 * unlabelled way out of the run.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Note, PressableCard, theme } from '@/shared/ui';

import type { Sport } from '../domain/Sport';
import { toggleSport } from '../domain/onboardingPass';
import { useOnboardingPass } from '../store/onboardingPass.store';
import { useSports } from '../hooks/useSports';
import { useStartAssessment } from '../hooks/useStartAssessment';

import { OnboardingChrome } from './OnboardingChrome';
import { onboardingErrorMessage } from './onboardingErrorMessage';
import { sportColour, sportLabel } from './sportPresentation';

export function SportsPickerScreen() {
  const router = useRouter();
  const sports = useSports();
  /**
   * The selection is this screen's own state, not a pass. A player still choosing has not
   * begun a walk through onboarding — they can add sports, remove them and leave — and the
   * pass begins on continue, with what they settled on. Ordering is `toggleSport`'s, so
   * "the first sport tapped is the first assessment" stays a tested rule rather than an
   * accident of how the array was built.
   */
  const [queue, setQueue] = useState<readonly Sport[]>([]);
  const toggle = (sport: Sport) => setQueue((chosen) => toggleSport(chosen, sport));
  const beginPass = useOnboardingPass((state) => state.begin);
  const start = useStartAssessment();

  const [first] = queue;

  const begin = () => {
    if (first === undefined) return;
    // The pass begins here, with the queue that was chosen. It no longer *clears* an
    // earlier walk — the entry gate ended that one when the player reached the app — so
    // this is a beginning rather than a reset that happened to double as one.
    beginPass(queue);
    start.mutate(first, {
      onSuccess: (step) =>
        router.replace({
          pathname: '/question/[assessmentId]',
          params: { assessmentId: step.assessmentId, sport: first },
        }),
    });
  };

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <OnboardingChrome eyebrow="Raketa" title="Which sports do you play?" />

      <ScrollView contentContainerStyle={s.content}>
        {/* Paused, not loading: `networkMode: 'online'` holds a query rather than
            failing it, so an offline player would otherwise watch a spinner forever. */}
        {sports.fetchStatus === 'paused' ? (
          <Note variant="amber">
            You&apos;re offline. The sports will load as soon as you&apos;re back.
          </Note>
        ) : null}

        {sports.isPending && sports.fetchStatus !== 'paused' ? (
          <ActivityIndicator accessibilityLabel="Loading sports" color={theme.color.muted} />
        ) : null}

        {sports.data?.length === 0 ? (
          <Note variant="amber">No sports are available to rate right now. Try again later.</Note>
        ) : null}

        {sports.error !== null ? (
          <View style={s.failure}>
            <Note variant="coral" accessibilityRole="alert">
              {onboardingErrorMessage(sports.error)}
            </Note>
            <Button label="Try again" variant="secondary" onPress={() => void sports.refetch()} />
          </View>
        ) : null}

        {sports.data?.map((sport) => (
          <SportCard
            key={sport}
            sport={sport}
            selected={queue.includes(sport)}
            onPress={() => toggle(sport)}
          />
        ))}
      </ScrollView>

      <View style={s.action}>
        {start.error !== null ? (
          <Note variant="coral" accessibilityRole="alert">
            {onboardingErrorMessage(start.error)}
          </Note>
        ) : null}

        <Button
          label={continueLabel(queue.length)}
          size="lg"
          disabled={first === undefined}
          busy={start.isPending}
          busyLabel="Starting…"
          onPress={begin}
        />
      </View>
    </SafeAreaView>
  );
}

/** The count is on the control, so nobody continues wondering what they just chose. */
function continueLabel(count: number): string {
  if (count === 0) return 'Choose a sport to continue';
  return count === 1 ? 'Rate 1 sport' : `Rate ${count} sports`;
}

interface SportCardProps {
  readonly sport: Sport;
  readonly selected: boolean;
  readonly onPress: () => void;
}

/**
 * Selection is carried by a **word** as well as by the border, because a state that
 * exists only as a colour excludes whoever cannot see that colour — and the border alone
 * would be exactly that.
 */
function SportCard({ sport, selected, onPress }: SportCardProps) {
  return (
    <PressableCard
      onPress={onPress}
      selected={selected}
      accessibilityLabel={sportLabel(sport)}
      accessibilityHint={selected ? 'Removes this sport' : 'Adds this sport'}
      style={s.sportCard}
    >
      <View style={[s.dot, { backgroundColor: sportColour(sport) }]} />
      <Text style={s.sportName}>{sportLabel(sport)}</Text>
      {selected ? <Text style={s.selectedMark}>Selected</Text> : null}
    </PressableCard>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  failure: { gap: theme.space.sm },
  sportCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
  },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  sportName: { ...theme.type.h2, color: theme.color.ink, flex: 1 },
  selectedMark: {
    ...theme.type.eyebrow,
    color: theme.color.ink,
    textTransform: 'uppercase',
  },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
});
