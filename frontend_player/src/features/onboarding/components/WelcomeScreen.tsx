/**
 * Welcome — what is about to happen, before it happens.
 *
 * The player is about to answer questions in a flow whose length they cannot see — the
 * engine decides it has heard enough one answer at a time. Saying what is coming first is
 * what makes that feel deliberate rather than sprung on them: a starting level per sport,
 * about a minute each.
 *
 * **Two cards, and the screen stops there.** *Nothing here is permanent* and the note about
 * answering for a normal match were both true and both cut: this screen's job is to get a
 * player into the questionnaire, and the result screen says what a starting estimate is
 * worth at the moment there is one to say it about.
 */

import { useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, theme } from '@/shared/ui';

import { OnboardingChrome } from './OnboardingChrome';

const POINTS = [
  {
    title: 'You get a starting level for each sport',
    body: 'A Level, the range it probably sits in, and how confident we are in it — one rating per sport you play.',
  },
  {
    title: 'It takes about a minute per sport',
    body: 'A few questions, one at a time. How many depends on your answers: a first-timer is done after one.',
  },
] as const;

export function WelcomeScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <OnboardingChrome eyebrow="Raketa" title="Let's find your level" />

      <ScrollView contentContainerStyle={s.content}>
        {POINTS.map((point) => (
          <Card key={point.title} style={s.card}>
            <Text style={s.cardTitle}>{point.title}</Text>
            <Text style={s.body}>{point.body}</Text>
          </Card>
        ))}
      </ScrollView>

      <View style={s.action}>
        <Button
          label="Get started"
          size="lg"
          onPress={() => router.push('/sports')}
          accessibilityHint="Choose the sports you play"
        />
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
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
  },
});
