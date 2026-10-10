/**
 * **A yes's answer, off the wire** — `YesAnswerResponse`, which `POST /proposals/{id}/yes` and
 * `POST /seat-charges/{id}/confirmation` both answer (#541). Optional fields read absent as
 * `null`, the shape the domain decides by.
 */

import type { components } from '@/generated/schema';

import type { PaymentToConfirm, YesAnswer, YourPayment } from '../domain/fill';

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
    waitingForTheClub: wire.waiting_for_the_club,
    yourPayment: refused === null ? null : toYourPayment(refused),
    ...(awaited === null ? {} : { paymentAwaitedUntil: awaited }),
  };
}

/**
 * **This player's refused share** — the yes's answer's, and a game's details' (#557): the payment,
 * why, and their time to pay while it runs (#625), absent for a `null` and from an older server.
 */
export function toYourPayment(wire: Schemas['YourPaymentSchema']): YourPayment {
  const confirmBy = wire.confirm_by ?? null;
  return {
    seatChargeId: wire.seat_charge_id,
    refusal: wire.refusal,
    ...(confirmBy === null ? {} : { confirmBy }),
  };
}

type WireToConfirm =
  Schemas['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema'];

/**
 * One refused share waiting for the reader — the live yes it holds or reopened, the payment, and
 * their time to pay while it runs (#625; absent from an older server). A sport this build cannot
 * name, or a refusal that does not wait for the player, is left out.
 */
function toPaymentToConfirm(wire: WireToConfirm): PaymentToConfirm | undefined {
  const { refusal } = wire;
  if (refusal !== 'AUTHENTICATION_REQUIRED' && refusal !== 'DECLINED') return undefined;
  const yes = toLiveYes(wire);
  const confirmBy: string | null | undefined = wire.confirm_by;
  return yes === undefined
    ? undefined
    : {
        ...yes,
        seatChargeId: wire.seat_charge_id,
        refusal,
        ...(confirmBy === null || confirmBy === undefined ? {} : { confirmBy }),
      };
}

export function toPaymentsToConfirm(
  wire: Schemas['PaymentsToConfirmResponse'],
): readonly PaymentToConfirm[] {
  return wire.payments
    .map(toPaymentToConfirm)
    .filter((payment): payment is PaymentToConfirm => payment !== undefined);
}
