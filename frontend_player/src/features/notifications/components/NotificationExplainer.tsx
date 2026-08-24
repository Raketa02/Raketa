/**
 * The explainer itself: four cards and two controls, and nothing about where it
 * is being shown.
 *
 * One implementation for both of `ADR-0061`'s occasions — the onboarding screen
 * and the sheet a standby join raises — because the argument for turning
 * notifications on does not change with the furniture around it, and two copies
 * of it would drift the way the prototype's second card did.
 *
 * **The two controls are not a pair of buttons that do opposite things.**
 * *Turn on* spends the one system prompt this install gets; *Not now* spends
 * nothing, records nothing and asks the OS nothing at all. That asymmetry is the
 * whole decision `ADR-0061` took, so the declining control is wired to a
 * different callback rather than to the same one with a flag.
 *
 * *Turn on* is the primary and sits above *Not now*, which is the order the
 * closing screens use: the recommended way on is the easy one, and the way past
 * is a deliberate tap rather than a hidden one.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, theme } from '@/shared/ui';

import {
  EXPLAINER_POINTS,
  NOT_NOW_HINT,
  NOT_NOW_LABEL,
  TURN_ON_HINT,
  TURN_ON_LABEL,
} from './explainerCopy';

export interface NotificationExplainerProps {
  /** Fires the OS prompt. The only control in the app that may. */
  readonly onTurnOn: () => void;
  /** Asks nothing and keeps nothing. */
  readonly onNotNow: () => void;
  /**
   * The prompt is up, or the registration behind it is in flight.
   *
   * The `Button` primitive's own state and not a fourth control: between the tap
   * and the OS dialog appearing there is otherwise nothing to see, and a blocked
   * button is what stops one thumb spending the prompt twice.
   */
  readonly busy?: boolean;
}

export function NotificationExplainer({
  onTurnOn,
  onNotNow,
  busy = false,
}: NotificationExplainerProps) {
  return (
    <View style={s.body}>
      {EXPLAINER_POINTS.map((point) => (
        <Card key={point.title} style={s.card}>
          <Text style={s.cardTitle}>{point.title}</Text>
          <Text style={s.cardBody}>{point.body}</Text>
        </Card>
      ))}

      <View style={s.actions}>
        <Button
          label={TURN_ON_LABEL}
          size="lg"
          busy={busy}
          busyLabel="Asking your phone…"
          accessibilityHint={TURN_ON_HINT}
          onPress={onTurnOn}
        />
        <Button
          label={NOT_NOW_LABEL}
          variant="secondary"
          size="lg"
          disabled={busy}
          accessibilityHint={NOT_NOW_HINT}
          onPress={onNotNow}
        />
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.sm },
  card: { gap: theme.space.xxs },
  cardTitle: { ...theme.type.cardTitle, color: theme.color.ink },
  cardBody: { ...theme.type.tiny, color: theme.color.muted },
  actions: { gap: theme.space.sm, paddingTop: theme.space.md },
});
