/**
 * The moment the rating is worked out.
 *
 * **It is held on screen for a minimum time, and that is the whole reason it exists as a
 * screen.** Completion is one round trip and the engine's arithmetic is fast, so without a
 * floor this appears and leaves inside a frame or two — which a player reads as a glitch
 * rather than as the moment their Level came into existence. The floor is
 * `theme.motion.hold.calculating`, and it is deliberately not skipped under reduced motion:
 * nothing here moves except the indicator, and a held screen is not an animation.
 *
 * **One short line, and it names the Sport.** The line has to be readable inside the hold —
 * a sentence a player cannot finish before the screen leaves is worse than no sentence — so
 * the copy and the duration are one decision. Lengthening either means revisiting both
 * (design-system 12.1).
 *
 * **Nothing is offered and nothing can be left.** There is no close control and no way
 * back: the rating is already being created, and a control that appeared to cancel it would
 * be a promise this screen cannot keep.
 */

import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { theme } from '@/shared/ui';

import type { Sport } from '../domain/Sport';

import { sportLabel } from './sportPresentation';

export interface CalculatingScreenProps {
  readonly sport: Sport;
}

export function CalculatingScreen({ sport }: CalculatingScreenProps) {
  const line = `Working out your ${sportLabel(sport)} level…`;

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <View style={s.centre}>
        {/* Unlabelled: the line below is the accessible announcement, and an indicator
            naming the same thing would say it twice. */}
        <ActivityIndicator size="large" color={theme.color.coral} accessibilityElementsHidden />
        <Text style={s.line} accessibilityRole="header">
          {line}
        </Text>
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  centre: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.lg,
  },
  line: { ...theme.type.h1, color: theme.color.ink, textAlign: 'center' },
});
