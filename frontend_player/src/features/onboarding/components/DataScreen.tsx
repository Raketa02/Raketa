/**
 * The data screen: what was kept, and what is never done with it.
 *
 * **It reads nothing, writes nothing, and calls no endpoint.** That is a property of the
 * screen and not an omission — there is no hook here on purpose. It is the same argument
 * the evidence trail makes about the number, applied to the data: an app that shows its
 * working about a rating should show its working about what it kept to produce it.
 *
 * **It is not a consent form and must never become one.** Nothing is recorded, nothing is
 * agreed to, and there is no control here that means yes. What a consent covers —
 * retention, withdrawal, jurisdiction — is a legal question, and the match-proposals
 * opt-in is its own explicit, skippable step whenever it arrives. Folding either into a
 * screen the player passes through on the way out would collect an agreement nobody read.
 *
 * **"No one can hand-edit a Level" is an invariant, not reassurance** (`CONTEXT.md`): a
 * level is proved, never declared, and the domain refuses a manual write rather than
 * guarding one behind a permission. Saying so plainly is the last thing onboarding does,
 * because it is the rule the whole rating context is built on and the player is entitled
 * to know it.
 *
 * Finishing enters the app. The entry gate decides where that lands, exactly as it does
 * from every other exit in this flow.
 */

import { useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, Note, theme } from '@/shared/ui';

import { OnboardingChrome } from './OnboardingChrome';

const POINTS = [
  {
    title: 'What we keep',
    body: 'Your answers, the rating they produced, and which version of the rating engine produced it. That last one is what lets a rating be re-examined later — a number nobody can attribute is a number nobody can check.',
  },
  {
    title: 'What we never do with it',
    body: 'Your answers stay between you and Rakieta. They are not shared with other players, and they are never sold.',
  },
  {
    title: 'No one can hand-edit a Level',
    body: 'Not you, not another player, not Rakieta staff. A level is proved, never declared: it moves when real matches move it, and there is no way to type one in.',
  },
  {
    title: 'You can rate a sport again later',
    body: 'Any sport, whenever you like — including one you skipped today, and one you stopped part-way through. Nothing here was a one-shot exam.',
  },
] as const;

export function DataScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <OnboardingChrome eyebrow="Rakieta" title="What Rakieta keeps" />

      <ScrollView contentContainerStyle={s.content}>
        {POINTS.map((point) => (
          <Card key={point.title} style={s.card}>
            <Text style={s.cardTitle}>{point.title}</Text>
            <Text style={s.body}>{point.body}</Text>
          </Card>
        ))}

        <Note variant="info">
          Your ratings live on your account, so they are there on your next phone and after a
          reinstall. Signing out on this device does not delete them.
        </Note>
      </ScrollView>

      <View style={s.action}>
        <Button
          label="Start playing"
          size="lg"
          onPress={() => router.replace('/')}
          accessibilityHint="Finishes setting up and opens Rakieta"
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
