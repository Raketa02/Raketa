/**
 * The payment port's two readings of Stripe — which key is Stripe's, and what the bank said — and
 * the laptop's provider, which the device port answers without calling anybody (#552).
 *
 * Stripe's SDK is jest's mock of it here (`jest.setup.js`), every call answering *no error*, so what
 * can be proved is what this file decides: never what Stripe does.
 */

import { bankAnswerOf, devicePayments, isStripeKey } from './payments';

const stripe = jest.requireMock<{
  readonly initStripe: jest.Mock;
  readonly createPaymentMethod: jest.Mock;
  readonly confirmSetupIntent: jest.Mock;
}>('@stripe/stripe-react-native');

beforeEach(() => jest.clearAllMocks());

describe('whose key it is', () => {
  it('is Stripe for a test or a live publishable key', () => {
    expect(isStripeKey('pk_test_51abc')).toBe(true);
    expect(isStripeKey('pk_live_51abc')).toBe(true);
  });

  it("is a provider with no phone half for anything else — the laptop's fake among them", () => {
    expect(isStripeKey('pk_fake_raketa')).toBe(false);
    expect(isStripeKey('')).toBe(false);
    expect(isStripeKey('sk_test_51abc')).toBe(false);
  });
});

describe('what the bank said', () => {
  it('saved, when Stripe answered without an error', () => {
    expect(bankAnswerOf({})).toBe('saved');
  });

  it('cancelled, when the player closed the check or the sheet', () => {
    expect(bankAnswerOf({ error: { code: 'Canceled' } })).toBe('cancelled');
  });

  it('declined, when the bank refused the card', () => {
    expect(bankAnswerOf({ error: { code: 'Failed', declineCode: 'generic_decline' } })).toBe(
      'declined',
    );
    expect(bankAnswerOf({ error: { code: 'Failed', stripeErrorCode: 'card_declined' } })).toBe(
      'declined',
    );
    expect(bankAnswerOf({ error: { code: 'Failed', type: 'card_error' } })).toBe('declined');
  });

  it('failed, for anything else — the network among it', () => {
    expect(bankAnswerOf({ error: { code: 'Failed', type: 'api_connection_error' } })).toBe(
      'failed',
    );
    expect(bankAnswerOf({ error: { code: 'Unknown' } })).toBe('failed');
  });
});

describe("the laptop's provider", () => {
  it('takes the card and saves it without starting Stripe', async () => {
    const taking = await devicePayments.takeCard('pk_fake_raketa');
    expect(taking).toEqual({ kind: 'taken', card: { reference: null } });

    const answer = await devicePayments.confirmSetup({
      publishableKey: 'pk_fake_raketa',
      clientSecret: 'seti_fake_secret',
      with: { kind: 'card', card: { reference: null } },
    });
    expect(answer).toBe('saved');

    expect(stripe.initStripe).not.toHaveBeenCalled();
    expect(stripe.createPaymentMethod).not.toHaveBeenCalled();
    expect(stripe.confirmSetupIntent).not.toHaveBeenCalled();
  });
});

describe("Stripe's provider", () => {
  it('starts once per key, and confirms the card it took by reference', async () => {
    stripe.createPaymentMethod.mockResolvedValueOnce({ paymentMethod: { id: 'pm_123' } });

    const taking = await devicePayments.takeCard('pk_test_51abc');
    expect(taking).toEqual({ kind: 'taken', card: { reference: 'pm_123' } });

    await devicePayments.confirmSetup({
      publishableKey: 'pk_test_51abc',
      clientSecret: 'seti_1_secret_2',
      with: { kind: 'card', card: { reference: 'pm_123' } },
    });

    expect(stripe.initStripe).toHaveBeenCalledTimes(1);
    expect(stripe.initStripe).toHaveBeenCalledWith(
      expect.objectContaining({ publishableKey: 'pk_test_51abc', urlScheme: 'raketa' }),
    );
    expect(stripe.confirmSetupIntent).toHaveBeenCalledWith('seti_1_secret_2', {
      paymentMethodType: 'Card',
      paymentMethodData: { paymentMethodId: 'pm_123' },
    });
  });

  it('refuses a card Stripe could not take', async () => {
    stripe.createPaymentMethod.mockResolvedValueOnce({
      error: { code: 'Failed', message: 'Card details not complete' },
    });
    expect(await devicePayments.takeCard('pk_test_51abc')).toEqual({ kind: 'refused' });
  });
});
