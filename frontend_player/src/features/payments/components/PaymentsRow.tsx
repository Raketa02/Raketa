/**
 * **Payments, on the You tab** — the ACCOUNT group's row: its title, the method in one line, and
 * the door to the screen (#552; the screens A7; mock 40).
 *
 * The line is the saved method's: *Card •••• 4312* for a card typed in, the wallet's name for one
 * saved through it (*Google Pay*), *Not set up* for none — and, when the bank moved the card to
 * another brand, the same with *accept the terms again* after it, because until then no club can
 * charge it. It is drawn from the screen's own read, so a save on the screen is on the row the
 * moment the player comes back.
 */

import { useRouter } from 'expo-router';

import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowProps } from '@/shared/ui';

import { usePaymentMethod } from '../hooks/usePaymentMethod';

import { YOU_PAYMENTS_ROUTE } from './paymentRoutes';
import { PAYMENTS_TITLE, paymentsRowLine } from './paymentsCopy';

export type PaymentsRowProps = Pick<DoorRowProps, 'divided'>;

export function PaymentsRow({ divided }: PaymentsRowProps) {
  const router = useRouter();
  const read = usePaymentMethod();

  return (
    <DoorRow
      glyph="credit-card"
      title={PAYMENTS_TITLE}
      line={liveLine(read, paymentsRowLine)}
      divided={divided}
      onPress={() => router.push(YOU_PAYMENTS_ROUTE)}
    />
  );
}
