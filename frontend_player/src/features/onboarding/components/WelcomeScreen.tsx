/**
 * Welcome — what is about to happen, before it happens.
 *
 * The player is about to answer questions they cannot revise, in a flow whose length they
 * cannot see. Saying so first is what makes the irreversibility feel deliberate rather
 * than sprung on them: a starting level per sport, about a minute each, nothing
 * permanent, refined by real matches later.
 */

import { useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, Note, theme } from '@/shared/ui';

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
  {
    title: 'Nothing here is permanent',
    body: 'This is a starting hypothesis, not a verdict. Real matches are what narrow it, and you can rate a sport again later.',
  },
] as const;

export function WelcomeScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <OnboardingChrome eyebrow="Rakieta" title="Let's find your level" />

      <ScrollView contentContainerStyle={s.content}>
        {POINTS.map((point) => (
          <Card key={point.title} style={s.card}>
            <Text style={s.cardTitle}>{point.title}</Text>
            <Text style={s.body}>{point.body}</Text>
          </Card>
        ))}

        <Note variant="info">
          Answer for a normal match, not your best day — that is what the questions mean, and it is
          what makes the level useful.
        </Note>
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
