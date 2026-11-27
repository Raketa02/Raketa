/**
 * **A yes's answer, off the wire** — `YesAnswerResponse`, which `POST /proposals/{id}/yes` and
 * `POST /seat-charges/{id}/confirmation` both answer (#541). Optional fields read absent as
 * `null`, the shape the domain decides by.
 */

import type { components } from '@/generated/schema';

import type { PaymentToConfirm, YesAnswer, YourPayment } from '../domain/fill';
import type { TimeTo } from '../domain/vocabulary';

import { toLiveYes } from './liveYesMappers';

type Schemas = components['schemas'];

export function toYesAnswer(wire: Schemas['YesAnswerResponse']): YesAnswer {
  const booked = wire.booked ?? null;
  const refused = wire.your_payment ?? null;
  const awaited = wire.payment_awaited_until ?? null;
  return {
    proposalId: wire.proposal_id,
    openSeats: wire.open_seats,
    booked: booked === null ? null : { bookingId: booked.booking_id, gameId: booked.game_id },
    yourPayment: refused === null ? null : toYourPayment(refused),
    ...(awaited === null ? {} : { paymentAwaitedUntil: awaited }),
  };
}

/**
 * **This player's refused share** — the yes's answer's, and a game's details' (#557): the payment,
 * why, and their time while it runs (#625) and what it is for (#638), each absent for a `null` and
 * from an older server.
 */
export function toYourPayment(wire: Schemas['YourPaymentSchema']): YourPayment {
  const confirmBy = wire.confirm_by ?? null;
  const timeTo = wire.time_to ?? null;
  return {
    seatChargeId: wire.seat_charge_id,
    refusal: wire.refusal,
    ...(confirmBy === null ? {} : { confirmBy }),
    ...(timeTo === null ? {} : { timeTo }),
  };
}

type WireToConfirm =
  Schemas['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema'];

/**
 * One refused share waiting for the reader — the live yes it holds or reopened, the payment, and
 * their time while it runs (#625) with what it is for (#638), absent from an older server. A sport
 * this build cannot name, or a refusal that does not wait for the player, is left out.
 */
function toPaymentToConfirm(wire: WireToConfirm): PaymentToConfirm | undefined {
  const { refusal } = wire;
  if (refusal !== 'AUTHENTICATION_REQUIRED' && refusal !== 'DECLINED') return undefined;
  // The refused share's wire (`PaymentToConfirmSchema`) publishes no court kind, so its yes is read
  // as mixed: the row it feeds draws no kind.
  const yes = toLiveYes({ ...wire, indoor: null });
  const confirmBy: string | null | undefined = wire.confirm_by;
  const timeTo: TimeTo | null | undefined = wire.time_to;
  return yes === undefined
    ? undefined
    : {
        ...yes,
        seatChargeId: wire.seat_charge_id,
        refusal,
        ...(confirmBy === null || confirmBy === undefined ? {} : { confirmBy }),
        ...(timeTo === null || timeTo === undefined ? {} : { timeTo }),
      };
}

export function toPaymentsToConfirm(
  wire: Schemas['PaymentsToConfirmResponse'],
): readonly PaymentToConfirm[] {
  return toPaymentToConfirmRows(wire.payments);
}

/**
 * **The rows themselves** — their own read's, and Home's *TO CONFIRM*, which serves the same rows
 * (#815, #819): one reading for both, so the sheet and You › Payments never disagree on a payment.
 */
export function toPaymentToConfirmRows(
  rows: readonly WireToConfirm[],
): readonly PaymentToConfirm[] {
  return rows
    .map(toPaymentToConfirm)
    .filter((payment): payment is PaymentToConfirm => payment !== undefined);
}
