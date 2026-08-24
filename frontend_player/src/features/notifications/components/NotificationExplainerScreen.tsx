/**
 * The onboarding occasion: the permission explained before anything is fired.
 *
 * `ADR-0061` puts the ask **during onboarding** rather than in context, and says
 * why: with rungs 4–7 in the pool most people who are offered a seat never join
 * a standby list, so an ask that only fired there would leave most of the ladder
 * unreachable. It also names the cost — an onboarding ask reaches everyone at
 * the moment they have least reason to say yes — and takes it anyway.
 *
 * **It sits between the ratings and the data screen**, which is where a screen
 * that asks for something belongs. It cannot be folded into either neighbour:
 * the data screen's own record says it *"is not a consent form and must never
 * become one"*, and the done screen is an account of what the player just
 * produced. And it cannot go last: the data screen's control says *Start
 * playing*, and a screen after it would make that label a lie.
 *
 * **Both controls lead to the same place**, which is the rule stated as
 * navigation: refusing costs her the message and never a card, so there is no
 * second path, no consequence screen and nothing kept about the answer.
 *
 * `replace`, like every step in this flow: onboarding is walked forwards, and a
 * back gesture onto an ask that has already been spent would offer to spend it
 * again.
 */

import { useRouter } from 'expo-router';
import { ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenHeader, theme } from '@/shared/ui';

import { useNotificationAsk } from '../hooks/useNotificationAsk';

import { NotificationExplainer } from './NotificationExplainer';
import { EXPLAINER_EYEBROW, EXPLAINER_TITLE } from './explainerCopy';

export function NotificationExplainerScreen() {
  const router = useRouter();
  const { asking, turnOn } = useNotificationAsk();

  const onwards = () => router.replace('/data');

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      {/* No progress strip, like the two closing screens: nothing here measures a
          sport being rated, and a bar claiming otherwise would be the one dishonest
          thing this screen could say about the walk. */}
      <ScreenHeader title={EXPLAINER_TITLE} eyebrow={EXPLAINER_EYEBROW} />

      <ScrollView contentContainerStyle={s.content}>
        <NotificationExplainer
          busy={asking}
          onTurnOn={() => {
            void turnOn().then(onwards);
          }}
          onNotNow={onwards}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
  },
});
