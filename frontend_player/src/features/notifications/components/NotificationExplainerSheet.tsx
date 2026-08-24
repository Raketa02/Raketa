/**
 * The second occasion: the same explainer, raised over the screen she is on.
 *
 * `ADR-0061` asks again **at the first standby join**, which is the moment the
 * interruption has a reason — she has just told the platform she wants this
 * match, and being told when a seat frees is the second thing that buys her.
 *
 * A sheet rather than a screen, because she is in the middle of something: a
 * route would take her off the match she just queued for to answer a question
 * about her phone. Dismissal — the scrim, the close control, the Android back
 * gesture — all mean *Not now*, which is safe here for the reason `BottomSheet`
 * states: a sheet's dismissal is always its non-committal option, and this
 * sheet's non-committal option is the one that spends nothing.
 *
 * **Nothing raises it yet, and that is a fact about the build rather than about
 * this component.** No surface in v1 joins a standby queue — the contract has a
 * `DELETE` for a queue place and no way to take one — so the occasion this was
 * written for has no caller. It is asserted as a **rendering** rather than as a
 * flow, and the missing act is
 * [#132](https://github.com/Raketa02/Raketa/issues/132).
 */

import { ScrollView, StyleSheet } from 'react-native';

import { BottomSheet, theme, type FocusTarget } from '@/shared/ui';

import { useNotificationAsk } from '../hooks/useNotificationAsk';

import { NotificationExplainer } from './NotificationExplainer';
import { EXPLAINER_TITLE, SHEET_CLOSE_LABEL } from './explainerCopy';

export interface NotificationExplainerSheetProps {
  readonly visible: boolean;
  /** Dismissal, and *Not now*: the same act, because they mean the same thing. */
  readonly onDismiss: () => void;
  /** The control that raised it. Focus returns here when it closes. */
  readonly returnFocusTo?: FocusTarget;
}

export function NotificationExplainerSheet({
  visible,
  onDismiss,
  returnFocusTo,
}: NotificationExplainerSheetProps) {
  const { asking, turnOn } = useNotificationAsk();

  return (
    <BottomSheet
      visible={visible}
      onClose={onDismiss}
      title={EXPLAINER_TITLE}
      closeLabel={SHEET_CLOSE_LABEL}
      returnFocusTo={returnFocusTo}
    >
      {/* The sheet stops at 88% of the screen, so the four cards scroll on a small
          phone rather than pushing the two controls off the bottom of it. */}
      <ScrollView contentContainerStyle={s.content}>
        <NotificationExplainer
          busy={asking}
          onTurnOn={() => {
            void turnOn().then(onDismiss);
          }}
          onNotNow={onDismiss}
        />
      </ScrollView>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  content: { paddingBottom: theme.space.sm },
});
