/**
 * **The payment setup as a sheet** — what a first yes opens when nothing is saved
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A2.4; the mechanics §6.1,
 * §12.5).
 *
 * *Before your first yes, the app asks you once to save a payment method and accept the terms. Your
 * yes lands as soon as that is done* — so the four steps of You › Payments' state A open over the
 * deck, unchanged: the same checklist, the same orchestrator, one setup per visit. **The yes is the
 * caller's**: `onSaved` lands it, and closing the sheet drops it — the close control says so.
 *
 * The checklist is mounted only while the sheet is open, so every opening is a fresh visit, as a
 * return to the screen is. The sheet's content keeps the root's contexts only — the provider's port
 * and the query client — and reaches no navigation (ADR-0178).
 */

import { StyleSheet, Text, View } from 'react-native';

import { BottomSheet, theme } from '@/shared/ui';

import { usePaymentSetup } from '../hooks/usePaymentSetup';

import { PAYMENTS_COPY, PAYMENT_TERMS_VERSION } from './paymentsCopy';
import { SetupChecklist } from './SetupChecklist';

export interface PaymentSetupSheetProps {
  readonly visible: boolean;
  /** Closed before the method was saved: the yes waiting on it is dropped. */
  readonly onClose: () => void;
  /** The method is saved and the cache holds it: land the yes. */
  readonly onSaved: () => void;
}

export function PaymentSetupSheet({ visible, onClose, onSaved }: PaymentSetupSheetProps) {
  const words = PAYMENTS_COPY.setupSheet;
  return (
    // The card field is in it: a tap on the sheet keeps the keyboard (`BottomSheet`'s note).
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={words.title}
      closeLabel={words.close}
      keepsKeyboardOnTap
    >
      {visible ? (
        <View style={s.body}>
          <Text style={s.line}>{words.line}</Text>
          <Setup onSaved={onSaved} />
        </View>
      ) : null}
    </BottomSheet>
  );
}

function Setup({ onSaved }: { readonly onSaved: () => void }) {
  const setup = usePaymentSetup({
    termsVersion: PAYMENT_TERMS_VERSION,
    walletSheetLabel: PAYMENTS_COPY.walletSheet,
    onSaved,
  });
  return <SetupChecklist setup={setup} />;
}

const s = StyleSheet.create({
  body: { gap: theme.space.md },
  line: { ...theme.type.rlLabel, color: theme.color.muted },
});
