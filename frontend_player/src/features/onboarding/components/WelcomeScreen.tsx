/**
 * Welcome — what is about to happen, before it happens.
 *
 * **The title names the whole walk, not the half of it this screen opens.** Onboarding is
 * two parts: a questionnaire that produces a Skill rating per sport, and six social steps
 * that produce a Player profile. *Let's find your level* named the first and promised
 * nothing about the second, so a player who answered the questions arrived at the tags step
 * having been told they were done. *Let's set you up* is true of both, and it is the reason
 * the first card describes them in that order.
 *
 * **Four cards, and the last three are the product rather than the flow.** The first says
 * what the player is about to do and what it buys them; Value, Mission and Vision say what
 * they are joining. That is a deliberate change of subject: the first part of onboarding
 * asks somebody to answer questions about themselves before they have seen anything, and
 * the honest exchange for that is saying what the thing is for.
 *
 * Nothing here is a rule. What the questionnaire is worth is the result screen's to say at
 * the moment there is a rating to say it about, and this screen still stops before making
 * any claim about a number nobody has yet.
 */

import { useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, theme } from '@/shared/ui';

import { OnboardingChrome } from './OnboardingChrome';

/**
 * The opening card: both parts of the walk, and what they are for.
 *
 * Two paragraphs and **no title**. A heading here would be the screen's own title said a
 * second time in smaller type — the card is the answer to *what happens now*, which is the
 * question the title just asked.
 */
const WHAT_HAPPENS = [
  'Answer a few sport questions to estimate your starting skill level, then tell us a bit ' +
    'about yourself and how you like to play.',
  'This helps Raketa connect you with the right people and create a better experience — ' +
    'whether you play to compete or just for fun.',
] as const;

/**
 * What Raketa is, in the three words a product says about itself.
 *
 * They are titled cards rather than a list, because each is a claim of a different kind:
 * what the player gets, what the platform is trying to do, and where it is going. Run
 * together they would read as one paragraph of marketing; apart, each is short enough to be
 * held to.
 */
const WHAT_RAKETA_IS = [
  {
    title: 'Value',
    body: 'Find the right people to play with.',
  },
  {
    title: 'Mission',
    body: 'Make playing racket sports more social, accessible and engaging.',
  },
  {
    title: 'Vision',
    body: 'Build the social network for racket sports.',
  },
] as const;

export function WelcomeScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <OnboardingChrome eyebrow="Raketa" title="Let's set you up" />

      <ScrollView contentContainerStyle={s.content}>
        {/* One accessibility element: two paragraphs of one statement read a screen apart
            are two fragments, and the second does not stand up without the first. */}
        <Card style={s.card}>
          <View accessible accessibilityLabel={WHAT_HAPPENS.join(' ')}>
            {WHAT_HAPPENS.map((paragraph, index) => (
              <Text key={paragraph} style={[s.body, index > 0 ? s.paragraph : undefined]}>
                {paragraph}
              </Text>
            ))}
          </View>
        </Card>

        {WHAT_RAKETA_IS.map((claim) => (
          // The title and the sentence under it are one thing to read — the same
          // obligation the opt-in card's promises carry, and it does not depend on the
          // layout being a row.
          <Card key={claim.title} style={s.card}>
            <View accessible accessibilityLabel={`${claim.title}. ${claim.body}`}>
              <Text style={s.cardTitle}>{claim.title}</Text>
              <Text style={[s.body, s.claimBody]}>{claim.body}</Text>
            </View>
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
  // The gap between two paragraphs of one statement, inside the element that holds both.
  paragraph: { marginTop: theme.space.sm },
  claimBody: { marginTop: theme.space.xxs },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
  },
});
