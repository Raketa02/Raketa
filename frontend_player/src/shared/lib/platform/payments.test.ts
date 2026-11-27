/**
 * The payment port's two readings of Stripe — which key is Stripe's, and what the bank said — and
 * the laptop's provider, which the device port answers without calling anybody (#552).
 *
 * Stripe's SDK is jest's mock of it here (`jest.setup.js`), every call answering *no error*, so what
 * can be proved is what this file decides: never what Stripe does.
 */

import TextInputState from 'react-native/Libraries/Components/TextInput/TextInputState';

import { dismissKeyboard } from './keyboard';

import {
  bankAnswerOf,
  devicePayments,
  isStripeKey,
  rememberCardFocus,
  releaseCardFocus,
} from './payments';

jest.mock('react-native/Libraries/Components/TextInput/TextInputState', () => ({
  __esModule: true,
  default: { currentlyFocusedInput: jest.fn(), blurInput: jest.fn() },
}));

const focus = TextInputState as unknown as {
  readonly currentlyFocusedInput: jest.Mock;
  readonly blurInput: jest.Mock;
};

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
    expect(isStripeKey('pk_fake_rakieta')).toBe(false);
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
    const taking = await devicePayments.takeCard('pk_fake_rakieta');
    expect(taking).toEqual({ kind: 'taken', card: { reference: null } });

    const answer = await devicePayments.confirmSetup({
      publishableKey: 'pk_fake_rakieta',
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
      expect.objectContaining({ publishableKey: 'pk_test_51abc', urlScheme: 'rakieta' }),
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

describe('preparing the provider before its fields are drawn', () => {
  it('starts Stripe with a Stripe key, and answers yes', async () => {
    await expect(devicePayments.prepare('pk_test_prepare_1')).resolves.toBe(true);
    expect(stripe.initStripe).toHaveBeenCalledTimes(1);
    expect(stripe.initStripe).toHaveBeenCalledWith(
      expect.objectContaining({ publishableKey: 'pk_test_prepare_1' }),
    );
  });

  it('answers no, rather than rejecting, when Stripe will not start', async () => {
    stripe.initStripe.mockRejectedValueOnce(new Error('no configuration'));

    await expect(devicePayments.prepare('pk_live_prepare_2')).resolves.toBe(false);
  });

  it('starts nothing for the laptop’s key', async () => {
    await expect(devicePayments.prepare('pk_fake_rakieta')).resolves.toBe(true);
    expect(stripe.initStripe).not.toHaveBeenCalled();
  });
});

describe('releasing the card field’s focus before its view goes', () => {
  beforeEach(() => focus.blurInput.mockClear());

  it('forgets a focus the card field took, without sending a native blur', () => {
    const field = {};
    focus.currentlyFocusedInput.mockReturnValue(field);

    rememberCardFocus();
    releaseCardFocus();

    expect(focus.blurInput).toHaveBeenCalledWith(field);
  });

  it('leaves another input’s focus alone', () => {
    focus.currentlyFocusedInput.mockReturnValue({});
    rememberCardFocus();

    focus.currentlyFocusedInput.mockReturnValue({ another: 'input' });
    releaseCardFocus();

    expect(focus.blurInput).not.toHaveBeenCalled();
  });

  it('does nothing when the card field never took focus', () => {
    focus.currentlyFocusedInput.mockReturnValue(null);

    releaseCardFocus();

    expect(focus.blurInput).not.toHaveBeenCalled();
  });

  it('releases before the card is taken, while the field is still on screen', async () => {
    const field = {};
    focus.currentlyFocusedInput.mockReturnValue(field);
    rememberCardFocus();
    const createPaymentMethod = jest.requireMock<{ createPaymentMethod: jest.Mock }>(
      '@stripe/stripe-react-native',
    ).createPaymentMethod;

    await devicePayments.takeCard('pk_test_focus_1');

    expect(focus.blurInput.mock.invocationCallOrder[0]).toBeLessThan(
      createPaymentMethod.mock.invocationCallOrder[0] ?? Infinity,
    );
  });
});

describe('asking the phone for its wallet on Android', () => {
  it('offers no Google Pay, and never asks the SDK, before Stripe has started', async () => {
    let fresh: typeof import('./payments') | undefined;
    jest.isolateModules(() => {
      fresh = jest.requireActual<typeof import('./payments')>('./payments');
    });
    const { Platform } = jest.requireActual<typeof import('react-native')>('react-native');
    jest.replaceProperty(Platform, 'OS', 'android');
    const sdk = jest.requireMock<{ isPlatformPaySupported: jest.Mock }>(
      '@stripe/stripe-react-native',
    );
    sdk.isPlatformPaySupported.mockClear();

    const wallet = await fresh?.devicePayments.phoneWallet();

    expect(wallet).toBeNull();
    expect(sdk.isPlatformPaySupported).not.toHaveBeenCalled();

    // The control: once Stripe has started, the same platform does ask the SDK — so the test above
    // is about the Android rule and not about a platform that never asks.
    await fresh?.devicePayments.prepare('pk_test_wallet_control');
    sdk.isPlatformPaySupported.mockResolvedValueOnce(true);
    await expect(fresh?.devicePayments.phoneWallet()).resolves.toBe('GOOGLE_PAY');
    expect(sdk.isPlatformPaySupported).toHaveBeenCalledTimes(1);
  });
});

describe('starting the provider for the laptop’s placeholder key', () => {
  it('starts Stripe on Android, so the native card field has a configuration when it mounts', async () => {
    const { Platform } = jest.requireActual<typeof import('react-native')>('react-native');
    const sdk = jest.requireMock<{ initStripe: jest.Mock }>('@stripe/stripe-react-native');
    jest.replaceProperty(Platform, 'OS', 'android');
    sdk.initStripe.mockClear();
    let fresh: typeof import('./payments') | undefined;
    jest.isolateModules(() => {
      fresh = jest.requireActual<typeof import('./payments')>('./payments');
    });

    await expect(fresh?.devicePayments.prepare('pk_fake_rakieta')).resolves.toBe(true);
    expect(sdk.initStripe).toHaveBeenCalledWith(
      expect.objectContaining({ publishableKey: 'pk_fake_rakieta' }),
    );
  });

  it('leaves iOS as it was: the placeholder key starts nothing', async () => {
    const { Platform } = jest.requireActual<typeof import('react-native')>('react-native');
    const sdk = jest.requireMock<{ initStripe: jest.Mock }>('@stripe/stripe-react-native');
    jest.replaceProperty(Platform, 'OS', 'ios');
    sdk.initStripe.mockClear();
    let fresh: typeof import('./payments') | undefined;
    jest.isolateModules(() => {
      fresh = jest.requireActual<typeof import('./payments')>('./payments');
    });

    await expect(fresh?.devicePayments.prepare('pk_fake_rakieta')).resolves.toBe(true);
    expect(sdk.initStripe).not.toHaveBeenCalled();
  });
});

describe('dismissing the keyboard while the card field holds focus', () => {
  it('clears the card field’s focus record before the keyboard is dismissed', () => {
    const { Keyboard } = jest.requireActual<typeof import('react-native')>('react-native');
    const order: string[] = [];
    const card = {};
    focus.blurInput.mockClear();
    focus.blurInput.mockImplementation(() => order.push('release'));
    jest.spyOn(Keyboard, 'dismiss').mockImplementation(() => order.push('dismiss'));
    focus.currentlyFocusedInput.mockReturnValue(card);
    rememberCardFocus();

    dismissKeyboard();

    expect(focus.blurInput).toHaveBeenCalledWith(card);
    expect(order).toEqual(['release', 'dismiss']);
    jest.restoreAllMocks();
    focus.blurInput.mockImplementation(() => undefined);
  });
});
