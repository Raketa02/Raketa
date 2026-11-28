/**
 * **You › Account › Payments, walked the way a player walks it** — the real route tree, the real
 * bar, and only `fetch` and the payment provider's phone half faked
 * ([#552](https://github.com/Rakieta02/Rakieta/issues/552); the screens A7.3; the mechanics §12.5).
 *
 * The provider is `fakePayments()`, which behaves as Stripe's test cards do: the number typed into
 * its field decides whether the bank saves the card, checks it first, or refuses it. The server is
 * the three writes of #536 in their order — `…/setup`, `…/terms` (the secret), `…/confirmation` —
 * and what the suite proves is the order the screen makes them in, the step that asks the bank by
 * itself, and the two states the one read draws.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { ActivityIndicator } from 'react-native';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel } from '@/shared/ui';
import {
  PAYMENT_METHOD_PATH,
  PAYMENT_TERMS_IN_FORCE,
  launchSignedIn,
  resetPayments,
  stubGate,
  stubOwnRecord,
  stubPaymentMethod,
  stubPayments,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  FAKE_CARD_NUMBER,
  TEST_CARDS,
  fakePayments,
  type FakePayments,
} from '@/test-support/platform';
import {
  installTransport,
  json,
  neverResponds,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import type { SetupStepName, SetupStepState } from '../domain/setupSteps';

import {
  PAYMENTS_COPY,
  PAYMENTS_TITLE,
  PAYMENT_TERMS_VERSION,
  inUseLine,
  keepsWorkingLine,
  stepLabel,
} from './paymentsCopy';

const SETUP_PATH = '/api/v1/players/me/payment-methods/setup';
const TERMS_PATH = '/api/v1/players/me/payment-methods/terms';
const CONFIRMATION_PATH = '/api/v1/players/me/payment-methods/confirmation';

const SECRET = 'seti_1_secret_abc';

/** The terms in force since Q113 — the mechanics §12.5, version `2026-10-10` (#635, #637). */
const TERMS_IN_FORCE =
  'When a game you said yes to fills, the club it is played at holds your share on your card — ' +
  'the court’s price divided by the players. If that hold would not last until the club’s ' +
  'cut-off, your card is checked when the game fills (your share held for a moment and let go), ' +
  'and your share is held four days before the cut-off. Your share is taken at the club’s ' +
  'cut-off. Leave before the cut-off and nothing is taken. After the cut-off your seat is ' +
  'offered to others; if someone takes it, you get your share back less what was kept on your ' +
  'payment, and you see the exact sum before you leave. If a game is still missing a player at ' +
  'the cut-off, it is called off and nothing is taken.';

const VISA_4312: Wire['SavedMethodSchema'] = { brand: 'visa', last_four: '4312', wallet: null };

/** One rated sport — a player past onboarding, whom the gate lets into the app. */
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

let transport: Transport;
let phone: FakePayments;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
  phone = fakePayments();
  stubPayments(phone);
});

afterEach(async () => {
  transport.restore();
  resetPayments();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/**
 * The server's three writes, each answering as #536's routes do — and the confirmation saving
 * whatever `saved` says, so the read that follows it is the server's too.
 */
function stubTheSetupRoutes(
  saved: Wire['SavedMethodSchema'] = { ...VISA_4312, last_four: '4242' },
) {
  transport.on('POST', SETUP_PATH, () =>
    json<Wire['PaymentSetupResponse']>(
      {
        setup_id: 'seti_1',
        publishable_key: 'pk_test_rakieta',
        terms_version: PAYMENT_TERMS_IN_FORCE,
      },
      201,
    ),
  );
  transport.on('POST', TERMS_PATH, () =>
    json<Wire['PaymentTermsResponse']>({ client_secret: SECRET }),
  );
  transport.on('POST', CONFIRMATION_PATH, () => {
    stubPaymentMethod(transport, saved);
    return json<Wire['PaymentMethodResponse']>({
      method: saved,
      terms_needed: false,
      terms_version: PAYMENT_TERMS_IN_FORCE,
    });
  });
}

const rowLabel = (line: string) => doorRowLabel(PAYMENTS_TITLE, line);

/** A signed-in player on You › Payments, the row's line read on the way. */
async function onPayments(rowLine: string) {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  fireEvent.press(await screen.findByLabelText(rowLabel(rowLine)));
}

/** A step's spoken name, as the checklist gives it. */
const step = (number: number, name: SetupStepName, state: SetupStepState, aside?: string): string =>
  stepLabel({ number, name, state }, aside);

const press = (label: string) => fireEvent.press(screen.getByLabelText(label));

/** Whether the button with this name is shut — disabled or busy, as a screen reader hears it. */
const shut = (label: string): boolean =>
  screen.getByLabelText(label).props.accessibilityState.disabled === true;

/** Step 1 with a card, Continue, the test card typed, and *Save the card*. */
async function throughTheCard(number: string = TEST_CARDS.saves) {
  press('Card');
  press(PAYMENTS_COPY.continue);
  fireEvent.changeText(await screen.findByLabelText(FAKE_CARD_NUMBER), number);
  press(PAYMENTS_COPY.saveTheCard);
  await screen.findByLabelText(step(3, 'terms', 'open'));
}

// ---------------------------------------------------------------------------
// The row
// ---------------------------------------------------------------------------

describe('the Payments row, in the ACCOUNT group', () => {
  it('says Not set up with nothing saved, under ACCOUNT', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));

    expect(await screen.findByLabelText(rowLabel('Not set up'))).toBeTruthy();
    expect(screen.getByText('Account')).toBeTruthy();
  });

  it('names a typed card by its last four, and a wallet by its name', async () => {
    stubPaymentMethod(transport, VISA_4312);
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));
    expect(await screen.findByLabelText(rowLabel('Card •••• 4312'))).toBeTruthy();
  });

  it('names a card saved through the phone’s wallet by the wallet', async () => {
    stubPaymentMethod(transport, { brand: 'mastercard', last_four: '5100', wallet: 'GOOGLE_PAY' });
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));
    expect(await screen.findByLabelText(rowLabel('Google Pay'))).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// State A — the four steps
// ---------------------------------------------------------------------------

describe('state A — a numbered checklist, in the order Q82 set', () => {
  it('opens on step 1 with the other three to come, and offers a card and BLIK', async () => {
    await onPayments('Not set up');

    expect(await screen.findByLabelText(step(1, 'choose', 'open'))).toBeTruthy();
    expect(screen.getByLabelText(step(2, 'card', 'waiting'))).toBeTruthy();
    expect(screen.getByLabelText(step(3, 'terms', 'waiting'))).toBeTruthy();
    expect(screen.getByLabelText(step(4, 'bank', 'waiting'))).toBeTruthy();

    expect(screen.getByLabelText('Card')).toBeTruthy();
    expect(screen.getByLabelText('BLIK')).toBeTruthy();
    // A phone with no wallet offers none.
    expect(screen.queryByLabelText('Google Pay')).toBeNull();
    expect(screen.queryByLabelText('Apple Pay')).toBeNull();
    // Nothing chosen, nothing to continue with.
    expect(shut(PAYMENTS_COPY.continue)).toBe(true);
  });

  it('shows BLIK’s notice and cannot continue with it — and opens no setup', async () => {
    await onPayments('Not set up');

    fireEvent.press(await screen.findByLabelText('BLIK'));

    expect(screen.getByText(PAYMENTS_COPY.blikNotice)).toBeTruthy();
    expect(shut(PAYMENTS_COPY.continue)).toBe(true);
    press(PAYMENTS_COPY.continue);
    expect(transport.requestsTo('POST', SETUP_PATH)).toHaveLength(0);

    // Choosing a card takes the notice away and lets the player on.
    press('Card');
    expect(screen.queryByText(PAYMENTS_COPY.blikNotice)).toBeNull();
    expect(shut(PAYMENTS_COPY.continue)).toBe(false);
  });

  it('starts the provider with the setup’s key before the card fields are drawn', async () => {
    stubTheSetupRoutes();
    await onPayments('Not set up');

    fireEvent.press(await screen.findByLabelText('Card'));
    press(PAYMENTS_COPY.continue);

    expect(await screen.findByLabelText(FAKE_CARD_NUMBER)).toBeTruthy();
    expect(phone.prepared).toEqual(['pk_test_rakieta']);
  });

  it('says the card could not be taken, in the sheet, when the provider throws rather than answers', async () => {
    stubTheSetupRoutes();
    await onPayments('Not set up');

    fireEvent.press(await screen.findByLabelText('Card'));
    press(PAYMENTS_COPY.continue);
    fireEvent.changeText(await screen.findByLabelText(FAKE_CARD_NUMBER), '4242 4242 4242 4242');
    Object.assign(phone, { takeCard: () => Promise.reject(new Error('native module went away')) });

    press(PAYMENTS_COPY.saveTheCard);

    expect(await screen.findByText(PAYMENTS_COPY.failures.CARD_REFUSED)).toBeTruthy();
    expect(screen.getByLabelText(FAKE_CARD_NUMBER)).toBeTruthy();
    expect(screen.getByLabelText(step(2, 'card', 'open'))).toBeTruthy();
  });

  it('walks a card through the four steps: setup, card, terms, then the bank by itself', async () => {
    stubTheSetupRoutes();
    await onPayments('Not set up');

    fireEvent.press(await screen.findByLabelText('Card'));
    press(PAYMENTS_COPY.continue);

    // Step 2: Stripe's fields, and *Save the card* shut until they hold a whole card.
    const fields = await screen.findByLabelText(FAKE_CARD_NUMBER);
    expect(screen.getByLabelText(step(1, 'choose', 'done', 'Card'))).toBeTruthy();
    expect(screen.getByLabelText(step(2, 'card', 'open'))).toBeTruthy();
    expect(transport.requestsTo('POST', SETUP_PATH)).toHaveLength(1);
    expect(shut(PAYMENTS_COPY.saveTheCard)).toBe(true);

    fireEvent.changeText(fields, '4242 4242');
    expect(shut(PAYMENTS_COPY.saveTheCard)).toBe(true);
    fireEvent.changeText(fields, '4242 4242 4242 4242');
    press(PAYMENTS_COPY.saveTheCard);

    // Step 3: the terms, before anything is saved — and nothing asked of the terms route yet.
    expect(await screen.findByLabelText(step(3, 'terms', 'open'))).toBeTruthy();
    expect(screen.getByLabelText(step(2, 'card', 'done'))).toBeTruthy();
    expect(screen.getByLabelText(TERMS_IN_FORCE)).toBeTruthy();
    expect(transport.requestsTo('POST', TERMS_PATH)).toHaveLength(0);
    expect(phone.confirmed).toEqual([]);

    press(PAYMENTS_COPY.accept);

    // Step 4 asked the bank by itself, with the secret the terms answered; this bank asks
    // nothing, so the method is saved and the screen is state B without another press.
    expect(await screen.findByText('Card •••• 4242')).toBeTruthy();
    expect(
      screen.getByText('Held when a game fills · taken by the club at its cut-off'),
    ).toBeTruthy();
    expect(transport.requestsTo('POST', TERMS_PATH).map((r) => r.body)).toEqual([
      { terms_version: '2026-10-10' },
    ]);
    expect(phone.confirmed).toEqual([SECRET]);
    expect(phone.checks).toBe(0);
    // The provider was opened with the key the setup answered, for the card and for the bank.
    expect(phone.keys).toEqual(['pk_test_rakieta', 'pk_test_rakieta']);
    expect(transport.requestsTo('POST', CONFIRMATION_PATH)).toHaveLength(1);
    // One setup for the whole walk — the card-testing guard counts them.
    expect(transport.requestsTo('POST', SETUP_PATH)).toHaveLength(1);
  });

  it('stays on step 4 when the player closes the bank’s check, and asks again on the button', async () => {
    stubTheSetupRoutes();
    phone.bank = 'closes';
    await onPayments('Not set up');

    await throughTheCard(TEST_CARDS.checksOnce);
    press(PAYMENTS_COPY.accept);

    expect(await screen.findByText(PAYMENTS_COPY.failures.BANK_CLOSED)).toBeTruthy();
    expect(screen.getByLabelText(step(4, 'bank', 'open'))).toBeTruthy();
    expect(screen.getByText(PAYMENTS_COPY.bankLine)).toBeTruthy();
    expect(transport.requestsTo('POST', CONFIRMATION_PATH)).toHaveLength(0);

    phone.bank = 'approves';
    press(PAYMENTS_COPY.askTheBank);

    expect(await screen.findByText('Card •••• 4242')).toBeTruthy();
    expect(phone.checks).toBe(2);
    // Asking again reused the setup and its one acceptance.
    expect(transport.requestsTo('POST', TERMS_PATH)).toHaveLength(1);
  });

  it('reopens the card details when the bank declines, and sends the next card straight to the bank', async () => {
    stubTheSetupRoutes();
    await onPayments('Not set up');

    await throughTheCard(TEST_CARDS.declines);
    press(PAYMENTS_COPY.accept);

    expect(await screen.findByText(PAYMENTS_COPY.failures.CARD_DECLINED)).toBeTruthy();
    expect(screen.getByLabelText(step(2, 'card', 'open'))).toBeTruthy();
    expect(screen.getByLabelText(step(3, 'terms', 'done'))).toBeTruthy();
    // The fields came back empty, so there is nothing to save until a card is typed again.
    expect(shut(PAYMENTS_COPY.saveTheCard)).toBe(true);

    fireEvent.changeText(screen.getByLabelText(FAKE_CARD_NUMBER), TEST_CARDS.saves);
    press(PAYMENTS_COPY.saveTheCard);

    expect(await screen.findByText('Card •••• 4242')).toBeTruthy();
    expect(transport.requestsTo('POST', TERMS_PATH)).toHaveLength(1);
    expect(transport.requestsTo('POST', SETUP_PATH)).toHaveLength(1);
  });

  it('shuts Accept, and says why, when the terms in force are not the words on this phone', async () => {
    stubTheSetupRoutes();
    transport.on('POST', SETUP_PATH, () =>
      json<Wire['PaymentSetupResponse']>(
        { setup_id: 'seti_1', publishable_key: 'pk_test_rakieta', terms_version: '2026-10-15' },
        201,
      ),
    );
    await onPayments('Not set up');

    await throughTheCard();

    expect(screen.getByText(PAYMENTS_COPY.failures.TERMS_OUTDATED)).toBeTruthy();
    expect(shut(PAYMENTS_COPY.accept)).toBe(true);
    press(PAYMENTS_COPY.accept);
    expect(transport.requestsTo('POST', TERMS_PATH)).toHaveLength(0);
  });

  it('says why the setup could not open — five a day — and stays on step 1', async () => {
    transport.on('POST', SETUP_PATH, () =>
      json({ code: 'payment_setups_exhausted', message: 'x', trace_id: 't', details: null }, 429),
    );
    await onPayments('Not set up');

    fireEvent.press(await screen.findByLabelText('Card'));
    press(PAYMENTS_COPY.continue);

    expect(
      await screen.findByText(PAYMENTS_COPY.refusals.payment_setups_exhausted as string),
    ).toBeTruthy();
    expect(screen.getByLabelText(step(1, 'choose', 'open'))).toBeTruthy();
  });
});

describe('state A — the phone’s wallet skips the card details', () => {
  it('offers the wallet, marks step 2 not needed, and saves through the wallet’s sheet', async () => {
    stubPayments((phone = fakePayments({ wallet: 'GOOGLE_PAY' })));
    stubTheSetupRoutes({ brand: 'mastercard', last_four: '5100', wallet: 'GOOGLE_PAY' });
    await onPayments('Not set up');

    fireEvent.press(await screen.findByLabelText('Google Pay'));
    press(PAYMENTS_COPY.continue);

    expect(await screen.findByLabelText(step(3, 'terms', 'open'))).toBeTruthy();
    expect(screen.getByLabelText(step(1, 'choose', 'done', 'Google Pay'))).toBeTruthy();
    expect(screen.getByLabelText(step(2, 'card', 'skipped', 'In Google Pay'))).toBeTruthy();
    expect(screen.queryByLabelText(FAKE_CARD_NUMBER)).toBeNull();

    press(PAYMENTS_COPY.accept);

    expect(await screen.findByText('GPay')).toBeTruthy();
    expect(screen.getByText('Card •••• 5100')).toBeTruthy();
    expect(phone.confirmed).toEqual([SECRET]);
  });

  it('keeps the player on step 4 when they close the wallet’s sheet', async () => {
    stubPayments((phone = fakePayments({ wallet: 'GOOGLE_PAY' })));
    phone.walletSheet = 'closes';
    stubTheSetupRoutes();
    await onPayments('Not set up');

    fireEvent.press(await screen.findByLabelText('Google Pay'));
    press(PAYMENTS_COPY.continue);
    fireEvent.press(await screen.findByLabelText(PAYMENTS_COPY.accept));

    expect(await screen.findByText(PAYMENTS_COPY.failures.BANK_CLOSED)).toBeTruthy();
    expect(transport.requestsTo('POST', CONFIRMATION_PATH)).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// State B — the saved method
// ---------------------------------------------------------------------------

describe('state B — the method card', () => {
  it('draws the brand, the last four, who charges it, and Change', async () => {
    stubPaymentMethod(transport, VISA_4312);
    await onPayments('Card •••• 4312');

    expect(await screen.findByText('VISA')).toBeTruthy();
    expect(screen.getByText('Card •••• 4312')).toBeTruthy();
    expect(screen.getByText(PAYMENTS_COPY.method.heldAndTaken)).toBeTruthy();
    expect(screen.getByLabelText(PAYMENTS_COPY.method.change)).toBeTruthy();
    expect(screen.getByLabelText(PAYMENTS_COPY.method.remove)).toBeTruthy();
    expect(screen.queryByLabelText(step(1, 'choose', 'open'))).toBeNull();
  });

  it('Change reopens the setup over the method still on file, and Keep this one closes it', async () => {
    stubPaymentMethod(transport, VISA_4312);
    await onPayments('Card •••• 4312');

    fireEvent.press(await screen.findByLabelText(PAYMENTS_COPY.method.change));

    expect(
      screen.getByText(keepsWorkingLine({ brand: 'visa', lastFour: '4312', wallet: null })),
    ).toBeTruthy();
    expect(screen.getByLabelText(step(1, 'choose', 'open'))).toBeTruthy();

    press(PAYMENTS_COPY.method.keep);
    expect(await screen.findByText('Card •••• 4312')).toBeTruthy();
    expect(screen.queryByLabelText(step(1, 'choose', 'open'))).toBeNull();
    // Nothing was removed on the way.
    expect(transport.requestsTo('DELETE', PAYMENT_METHOD_PATH)).toHaveLength(0);
  });

  it('Change saves a new card over the old one, which paid until then', async () => {
    stubPaymentMethod(transport, VISA_4312);
    stubTheSetupRoutes();
    await onPayments('Card •••• 4312');

    fireEvent.press(await screen.findByLabelText(PAYMENTS_COPY.method.change));
    await throughTheCard();
    press(PAYMENTS_COPY.accept);

    expect(await screen.findByText('Card •••• 4242')).toBeTruthy();
    expect(screen.queryByText('Card •••• 4312')).toBeNull();
    expect(transport.requestsTo('DELETE', PAYMENT_METHOD_PATH)).toHaveLength(0);

    // Back on the tab, the row says the new card.
    fireEvent.press(screen.getByLabelText('You'));
    expect(await screen.findByLabelText(rowLabel('Card •••• 4242'))).toBeTruthy();
  });

  it('removes the method when nothing needs it, and is state A again', async () => {
    stubPaymentMethod(transport, VISA_4312);
    transport.on('DELETE', PAYMENT_METHOD_PATH, () => noContent());
    await onPayments('Card •••• 4312');

    fireEvent.press(await screen.findByLabelText(PAYMENTS_COPY.method.remove));

    expect(await screen.findByLabelText(step(1, 'choose', 'open'))).toBeTruthy();
    expect(screen.queryByText('Card •••• 4312')).toBeNull();
    expect(transport.requestsTo('DELETE', PAYMENT_METHOD_PATH)).toHaveLength(1);
  });

  // `decisions.md` §3.7: the link swapped its word and nothing moved. Busy now, as a button is.
  it('says it is removing with its word and a spinner, and takes no second press', async () => {
    stubPaymentMethod(transport, VISA_4312);
    transport.on('DELETE', PAYMENT_METHOD_PATH, neverResponds());
    await onPayments('Card •••• 4312');

    fireEvent.press(await screen.findByLabelText(PAYMENTS_COPY.method.remove));

    const busy = await screen.findByLabelText(PAYMENTS_COPY.method.removing);
    expect(busy.props.accessibilityState).toMatchObject({ busy: true, disabled: true });
    expect(screen.UNSAFE_getByType(ActivityIndicator)).toBeTruthy();
    fireEvent.press(busy);
    expect(transport.requestsTo('DELETE', PAYMENT_METHOD_PATH)).toHaveLength(1);
  });

  it('refuses Remove with its reason while a live yes or a booked game needs the method', async () => {
    stubPaymentMethod(transport, VISA_4312);
    transport.on('DELETE', PAYMENT_METHOD_PATH, () =>
      json(
        {
          code: 'payment_method_in_use',
          message: 'x',
          trace_id: 't',
          details: { live_yeses: 2, upcoming_games: 1 },
        },
        409,
      ),
    );
    await onPayments('Card •••• 4312');

    fireEvent.press(await screen.findByLabelText(PAYMENTS_COPY.method.remove));

    const line = inUseLine({ liveYeses: 2, upcomingGames: 1 });
    expect(line).toBe(
      'It can’t be removed while it still pays for 2 live yeses and 1 booked game ahead.',
    );
    expect(await screen.findByText(line)).toBeTruthy();
    expect(screen.getByText('Card •••• 4312')).toBeTruthy();
  });

  /** Q113: the words changed, so a player who accepted the earlier ones accepts these (#637). */
  it('asks for the terms in force again of a player who accepted the earlier words', async () => {
    stubPaymentMethod(transport, VISA_4312, { termsNeeded: true });
    transport.on('POST', TERMS_PATH, () => {
      stubPaymentMethod(transport, VISA_4312);
      return json<Wire['PaymentTermsResponse']>({ client_secret: null });
    });
    await onPayments(`Card •••• 4312 · ${PAYMENTS_COPY.row.termsAgain}`);

    expect(await screen.findByText(PAYMENTS_COPY.method.termsAgainTitle)).toBeTruthy();
    expect(
      screen.getByText(
        'Clubs can’t hold your share on this card until you accept the terms in force — they changed, or your bank moved the card to another network.',
      ),
    ).toBeTruthy();
    expect(screen.getByText(TERMS_IN_FORCE)).toBeTruthy();

    press(PAYMENTS_COPY.method.termsAgain);

    await waitFor(() =>
      expect(screen.queryByText(PAYMENTS_COPY.method.termsAgainTitle)).toBeNull(),
    );
    expect(transport.requestsTo('POST', TERMS_PATH).map((r) => r.body)).toEqual([
      { terms_version: '2026-10-10' },
    ]);
  });

  it('asks for the terms again when the bank moved the card to another brand', async () => {
    stubPaymentMethod(transport, { ...VISA_4312, brand: 'mastercard' }, { termsNeeded: true });
    transport.on('POST', TERMS_PATH, () => {
      stubPaymentMethod(transport, { ...VISA_4312, brand: 'mastercard' });
      return json<Wire['PaymentTermsResponse']>({ client_secret: null });
    });
    await onPayments(`Card •••• 4312 · ${PAYMENTS_COPY.row.termsAgain}`);

    expect(await screen.findByText(PAYMENTS_COPY.method.termsAgainTitle)).toBeTruthy();
    expect(screen.getByText('MC')).toBeTruthy();

    press(PAYMENTS_COPY.method.termsAgain);

    await waitFor(() =>
      expect(screen.queryByText(PAYMENTS_COPY.method.termsAgainTitle)).toBeNull(),
    );
    expect(transport.requestsTo('POST', TERMS_PATH).map((r) => r.body)).toEqual([
      { terms_version: PAYMENT_TERMS_VERSION },
    ]);
    expect(screen.getByText('MC')).toBeTruthy();
  });
});
