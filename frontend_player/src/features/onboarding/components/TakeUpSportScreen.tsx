/**
 * The door's other side: one sport, taken up from the home screen.
 *
 * `ADR-0084` gives a player who taps a chip for a sport she holds no rating at
 * *"a destination rather than a better sentence"*, and this is the destination.
 * Now names it as a **route** and knows nothing else about it — the questionnaire,
 * the pass and the whole tail are this feature's, and a URL is the only thing
 * that crosses.
 *
 * ## It starts or resumes, and it does not know which
 *
 * `POST /assessments` is **idempotent per player and sport**: a start for a sport
 * that already has an unfinished run hands back that run's outstanding question
 * rather than opening a second one. So *"a parked run continues where it stopped,
 * however old"* is the server replaying a transcript, not a branch here — which is
 * exactly why the door's two codes differ in their **words** and in nothing else,
 * and why the phone is never asked to hold the rule (`ADR-0053`).
 *
 * ## The pass begins here, with its origin
 *
 * A walk begun at the door ends **back on Now, filtered to the sport it
 * produced**, where the first walk ends with the account of itself. Nothing
 * downstream can recover which of the two this is, so it is recorded when the
 * walk starts — see `PassOrigin`. It is recorded **on success**, so a start that
 * failed and was walked away from leaves no pass behind.
 *
 * ## Nothing is offered while it is in flight
 *
 * One request, and a held screen naming the sport — the same shape
 * `CalculatingScreen` uses for the other unavoidable wait in this flow. A cancel
 * control would be a promise this screen cannot keep: the run may already exist
 * on the server by the time it were pressed.
 */

import { useRouter } from 'expo-router';
import { useCallback, useEffect, useRef } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Note, theme } from '@/shared/ui';

import type { Sport } from '../domain/Sport';
import { useStartAssessment } from '../hooks/useStartAssessment';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { onboardingErrorMessage } from './onboardingErrorMessage';
import { sportLabel } from './sportPresentation';

export interface TakeUpSportScreenProps {
  readonly sport: Sport;
}

export function TakeUpSportScreen({ sport }: TakeUpSportScreenProps) {
  const router = useRouter();
  const beginPass = useOnboardingPass((state) => state.begin);
  const start = useStartAssessment();

  const startRun = start.mutate;
  // One start per visit to this screen, and a `replace` on the way out. Without
  // the latch a re-render while the request is in flight fires a second one, and
  // the server's idempotency would answer both — leaving two navigations racing
  // over one run.
  const asked = useRef(false);

  const open = useCallback(() => {
    if (asked.current) return;
    asked.current = true;

    startRun(sport, {
      onSuccess: (step) => {
        // Recorded before the navigation, because the question screen reads a
        // position on its very first render.
        beginPass([sport], 'door');
        router.replace({
          pathname: '/question/[assessmentId]',
          params: { assessmentId: step.assessmentId, sport },
        });
      },
      onError: () => {
        // Released, so the control below can genuinely try again.
        asked.current = false;
      },
    });
  }, [beginPass, router, sport, startRun]);

  // Once, on arrival: the door was the tap, and asking a player to press a second
  // button to start what she has just started is the app not listening. The latch
  // is inside `open`, so the effect firing twice — a re-render, StrictMode — costs
  // nothing, and the retry below goes through the same door.
  useEffect(open, [open]);

  if (start.error !== null) {
    return (
      <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
        <View style={s.content}>
          <Text style={s.title} accessibilityRole="header">
            We couldn&apos;t open the {sportLabel(sport)} questions
          </Text>
          <Note variant="coral" accessibilityRole="alert">
            {onboardingErrorMessage(start.error)}
          </Note>
          <Button label="Try again" size="lg" busy={start.isPending} onPress={open} />
          <Button label="Not now" variant="secondary" onPress={() => router.replace('/')} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <View style={s.centre}>
        {/* Unlabelled: the line below is the accessible announcement, and an
            indicator naming the same thing would say it twice. */}
        <ActivityIndicator size="large" color={theme.color.coral} accessibilityElementsHidden />
        <Text style={s.line} accessibilityRole="header">
          Opening your {sportLabel(sport)} questions…
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
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.md,
  },
  title: { ...theme.type.h1, color: theme.color.ink },
  line: { ...theme.type.h1, color: theme.color.ink, textAlign: 'center' },
});
