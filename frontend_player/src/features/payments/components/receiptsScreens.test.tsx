/**
 * **You › Payments' RECEIPTS, walked** — the real route tree with only `fetch` faked
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A7.3; mock 49): a share
 * taken, a refund with what was kept on the payment, and a hold let go (#644).
 *
 * **The day words are asserted on dates a week or more from the read**, where they are a date
 * whatever the clock says: the harness runs every pending timer on each navigation and moves the
 * fake clock with them — past midnight on the way to this screen — so *Today* and *Yesterday* are
 * the presentation test's (`receiptsPresentation.test.ts`), against a clock it holds.
 */

import { fireEvent, screen } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel } from '@/shared/ui';
import {
  RECEIPTS_PATH,
  launchSignedIn,
  stubGate,
  stubOwnRecord,
  stubPaymentMethod,
  stubProfileOptions,
  stubProfileSurface,
  stubReceipts,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { PAYMENTS_COPY, PAYMENTS_TITLE } from './paymentsCopy';

const WORDS = PAYMENTS_COPY.receipts;

/** Wednesday 30 September 2026, 10:00 in Warsaw. */
const READ_AT = Date.parse('2026-09-30T08:00:00Z');

const VISA_4312: Wire['SavedMethodSchema'] = { brand: 'visa', last_four: '4312', wallet: null };

const RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

function receipt(extra: Partial<Wire['ReceiptSchema']> = {}): Wire['ReceiptSchema'] {
  return {
    seat_charge_id: 'a2000000-0000-4000-8000-000000000001',
    kind: 'CHARGE',
    club: { id: 'b0000000-0000-4000-8000-000000000001', name: 'Bonarka Arena' },
    sport: 'PADEL',
    // Tuesday 20 October, 16:00 in Warsaw — booked weeks ahead.
    starts_at: '2026-10-20T14:00:00Z',
    amount_grosze: 2800,
    card_fee_grosze: null,
    paid_at: '2026-09-29T18:00:00Z',
    ...extra,
  };
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A signed-in player with a saved card, on You › Payments. */
async function onPayments() {
  stubPaymentMethod(transport, VISA_4312);
  await launchSignedIn();
  jest.setSystemTime(READ_AT);
  fireEvent.press(await screen.findByLabelText('You'));
  fireEvent.press(await screen.findByLabelText(doorRowLabel(PAYMENTS_TITLE, 'Card •••• 4312')));
}

describe('RECEIPTS', () => {
  it('draws each share paid — the club as the title, the game under it, the amount signed — newest first', async () => {
    stubReceipts(transport, [
      receipt(),
      receipt({
        seat_charge_id: 'a2000000-0000-4000-8000-000000000002',
        club: { id: 'b0000000-0000-4000-8000-000000000002', name: 'Ogrody 33' },
        sport: 'TENNIS',
        // Saturday 19 September, 18:00 in Warsaw — played.
        starts_at: '2026-09-19T16:00:00Z',
        amount_grosze: 2650,
      }),
    ]);
    await onPayments();

    expect(await screen.findByText('Bonarka Arena')).toBeTruthy();
    expect(screen.getByText('Padel · 20 Oct · 16:00')).toBeTruthy();
    expect(screen.getByText('−28 zł · paid')).toBeTruthy();
    expect(screen.getByLabelText('Bonarka Arena, Padel · 20 Oct · 16:00, 28 zł paid')).toBeTruthy();
    expect(screen.getByText('Tennis · 19 Sep · 18:00')).toBeTruthy();
    expect(screen.getByText('−26,50 zł · paid')).toBeTruthy();

    const rows = screen.getAllByTestId(/^receipt-/).map((row) => row.props.testID as string);
    expect(rows).toEqual([
      'receipt-a2000000-0000-4000-8000-000000000001',
      'receipt-a2000000-0000-4000-8000-000000000002',
    ]);
    // No BLIK line while BLIK isn't offered (Q113).
    expect(screen.getByText('Refunds can take up to two weeks to reach your card.')).toBeTruthy();
    expect(screen.queryByText(/BLIK/)).toBeNull();
  });

  /** Ivan left after the cut-off and Diego took his seat: 1,76 zł kept on his 40 zł (Q113). */
  it('draws a refund beside the share it gave back, with exactly what was kept on the payment under it', async () => {
    stubReceipts(transport, [
      receipt({
        kind: 'REFUND',
        amount_grosze: 3824,
        card_fee_grosze: 176,
        paid_at: '2026-09-30T18:00:00Z',
      }),
      receipt({ amount_grosze: 4000 }),
    ]);
    await onPayments();

    expect(await screen.findByText('+38,24 zł · refunded')).toBeTruthy();
    expect(screen.getByText('1,76 zł kept on your payment')).toBeTruthy();
    expect(screen.getByText('−40 zł · paid')).toBeTruthy();
    expect(
      screen.getByLabelText(
        'Bonarka Arena, Padel · 20 Oct · 16:00, 38,24 zł refunded, 1,76 zł kept on your payment',
      ),
    ).toBeTruthy();
    // A refunded share is two rows under one payment (#544).
    expect(screen.getAllByTestId('receipt-a2000000-0000-4000-8000-000000000001')).toHaveLength(2);
  });

  /** A leave before the cut-off: nothing was taken, and the hold the bank app showed is explained. */
  it('draws a hold let go, dated when it was, with nothing signed — nothing moved', async () => {
    stubReceipts(transport, [
      receipt({
        kind: 'RELEASED',
        amount_grosze: 4000,
        // Monday 28 September, 11:00 in Warsaw.
        paid_at: '2026-09-28T09:00:00Z',
      }),
    ]);
    await onPayments();

    expect(await screen.findByText('40 zł held · released')).toBeTruthy();
    expect(screen.getByText('Released 28 Sep')).toBeTruthy();
    expect(
      screen.getByLabelText('Bonarka Arena, Padel · 20 Oct · 16:00, 40 zł held, released 28 Sep'),
    ).toBeTruthy();
    expect(screen.queryByText(/[−+]40 zł/)).toBeNull();
  });

  it('says what will land here when nothing has, and keeps the footer for rows', async () => {
    await onPayments();

    expect(await screen.findByText(WORDS.empty)).toBeTruthy();
    expect(screen.getByRole('header', { name: WORDS.title })).toBeTruthy();
    expect(screen.queryByText(WORDS.footer)).toBeNull();
  });

  it('says why the read failed under the section’s name, and reads again on the retry', async () => {
    let refused = false;
    transport.on('GET', RECEIPTS_PATH, () => {
      if (refused) return json<Wire['ReceiptsResponse']>({ receipts: [receipt()] });
      refused = true;
      return errorResponse(429, 'rate_limited');
    });
    await onPayments();

    fireEvent.press(await screen.findByRole('button', { name: PAYMENTS_COPY.readAgain }));

    expect(await screen.findByText('Bonarka Arena')).toBeTruthy();
  });

  it('is not read in state A, where nothing is saved', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));
    fireEvent.press(await screen.findByLabelText(doorRowLabel(PAYMENTS_TITLE, 'Not set up')));

    expect(await screen.findByText('Choose how you pay')).toBeTruthy();
    expect(screen.queryByText(WORDS.empty)).toBeNull();
    expect(transport.requestsTo('GET', RECEIPTS_PATH)).toHaveLength(0);
  });
});
