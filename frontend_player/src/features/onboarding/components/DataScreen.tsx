/**
 * The data screen: what was kept, and what is never done with it.
 *
 * **It reads nothing, writes nothing, and calls no endpoint.** That is a property of the
 * screen and not an omission — there is no hook here on purpose. It is the same argument
 * the evidence trail makes about the number, applied to the data: an app that shows its
 * working about a rating should show its working about what it kept to produce it.
 *
 * **It accounts for the whole of what onboarding collected**, which is now two parts rather
 * than one. A screen that listed the questionnaire's answers and said nothing about the
 * tags, the photos, the week and the area that the second part collects would be a lie by
 * omission — the player handed those over a few screens ago and this is the screen that says
 * what became of them. The second part stopped asking how far a player will travel and
 * whether games may be suggested ([#582](https://github.com/Raketa02/Raketa/issues/582)), so
 * this screen keeps no account of either. **The gender answer is not on the card about what
 * another player sees**, because the step that asks it promised it never is.
 *
 * **It is not a consent form and must never become one.** Nothing is recorded, nothing is
 * agreed to, and there is no control here that means yes. What a consent covers —
 * retention, withdrawal, jurisdiction — is a legal question, and asking for one on the way
 * out would be collecting an agreement nobody read.
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
import { useHardwareBack } from '@/shared/lib/platform';

/**
 * What Raketa keeps, and what it never does with it — the whole of onboarding, in the order
 * a player gave it.
 *
 * Every claim below is one the app can be held to. The photos really are re-encoded on
 * arrival, which is why nothing they carried survives; the area really is rounded before
 * anything is written, on the phone and again on the platform. **Nothing here claims a check
 * nobody performs** — there is no sentence saying a photo is reviewed, because a promise
 * about moderation is a promise, not a description — and **nothing here promises a screen
 * that does not exist**: editing a Player profile is not built, so this table says what was
 * kept rather than what a player may go and change.
 */
const POINTS = [
  {
    title: 'What we keep from the questions',
    body: 'Your answers, the rating they produced, and which version of the rating engine produced it. That last one is what lets a rating be re-examined later — a number nobody can attribute is a number nobody can check.',
  },
  {
    title: 'What we keep from setting up',
    body: 'The tags you picked, the photos you added, the parts of the week you ticked and the area you play in. That is what lets another player see who they would be playing, and what lets Raketa look for them near you.',
  },
  {
    title: 'Your week is a preference, not a diary',
    body: 'It is used to work out when two players overlap, and it is never shown to anybody as a calendar. Nothing you ticked is a promise to be anywhere.',
  },
  {
    title: 'Your area is kept coarse, and your position is never shared',
    body: 'About a kilometre across — the exact reading your phone gave is rounded before anything is written down, on this phone and again on the platform, so nobody has it to show. Raketa never reads your location while you are somewhere else in your phone.',
  },
  {
    title: 'A photo arrives without the data behind it',
    body: 'Phones write the place and time into a picture. Every photo is re-encoded when it reaches Raketa, so what is stored is the picture and none of what was attached to it.',
  },
  {
    title: 'What we never do with any of it',
    body: 'It stays between you and Raketa. Your questionnaire answers are not shared with other players, and nothing here is ever sold.',
  },
  {
    title: 'No one can hand-edit a Level',
    body: 'Not you, not another player, not Raketa staff. A level is proved, never declared: it moves when real matches move it, and there is no way to type one in.',
  },
  {
    title: 'You can rate a sport again later',
    // Deliberately **not** a promise that the six answers above are editable. Editing a
    // Player profile is a screen this app does not have yet, and the steps that do promise
    // it — photos and location — promise only their own. A screen listing five things a
    // player cannot go and change would be the same untrue claim as a review nobody runs.
    body: 'Any sport, whenever you like — including one you skipped today, and one you stopped part-way through. Nothing here was a one-shot exam.',
  },
] as const;

export function DataScreen() {
  const router = useRouter();
  /**
   * **The device's back is claimed and refused, because this screen draws none.**
   *
   * Every screen in onboarding is reached by `replace`, so the group holds one entry per push
   * — and the push behind this one is the welcome screen, from which the only way forward is
   * to rate a sport again. An unclaimed press popped to exactly there.
   * [ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md): *"Back and
   * forward move freely inside each part and never cross between them."* A press that does
   * nothing is what the missing back control has already said.
   */
  useHardwareBack(() => {});

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <OnboardingChrome eyebrow="Raketa" title="What Raketa keeps" />

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
          accessibilityHint="Finishes setting up and opens Raketa"
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
