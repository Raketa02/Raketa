/**
 * The result route — where the question loop ends.
 *
 * **This is the terminus, not the screen.** #24 owns getting here: an assessment that has
 * no outstanding question left is finished, and the questionnaire `replace`s onto this
 * route rather than leaving the player on a question that no longer exists. The Level, the
 * likely range, the Confidence ring and the evidence trail are #25's, and the choice
 * between rating another sport and stopping here is #26's — so this screen deliberately
 * shows **no numbers at all** rather than a first draft of a rating that has to be read
 * with its uncertainty or not at all.
 *
 * `AssessmentStepResponse` already carries the result payload; it is not mapped, because a
 * field mapped for a screen that does not exist yet is a field no test covers.
 */

import { useRouter } from 'expo-router';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Note, theme } from '@/shared/ui';

import type { Sport } from '../domain/Sport';
import { ratingPosition } from '../domain/sportQueue';
import { useSportQueue } from '../store/sportQueue.store';

import { OnboardingChrome } from './OnboardingChrome';
import { sportLabel } from './sportPresentation';

export interface ResultScreenProps {
  readonly assessmentId: string;
  readonly sport: Sport;
}

export function ResultScreen({ sport }: ResultScreenProps) {
  const router = useRouter();
  const queue = useSportQueue((state) => state.queue);
  const position = ratingPosition(queue, sport);

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <OnboardingChrome
        eyebrow={`${sportLabel(sport)} · Rating ${position.index} of ${position.total}`}
        title="Your rating is ready"
        position={position}
      />

      <ScrollView contentContainerStyle={s.content}>
        <Note variant="mint">
          That&apos;s everything we need for {sportLabel(sport)}. Your starting level is saved.
        </Note>
      </ScrollView>

      <View style={s.action}>
        <Button label="Go to Rakieta" size="lg" onPress={() => router.replace('/')} />
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
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
  },
});
