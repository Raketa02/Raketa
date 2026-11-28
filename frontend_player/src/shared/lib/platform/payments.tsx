/**
 * The payment provider's phone half, behind a port. **The only module that imports
 * `@stripe/stripe-react-native`** ([#552](https://github.com/Rakieta02/Rakieta/issues/552); the
 * mechanics §12.4, §12.5; [ADR-0190](../../../../../docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md)).
 *
 * Saving a payment method is four steps, and two of them happen on the provider's side of the
 * phone: **the card is typed into Stripe's own fields** — the app never touches a card number — and
 * **the bank is asked** by Stripe's SDK, which draws the bank's one-time check itself or opens the
 * phone's wallet. Both are native, and a native module has no JS implementation a suite could
 * drive, so a screen that imported the SDK would be a screen no suite could walk to a saved card.
 * Hence a port, like the six beside it, with a fake in `src/test-support/platform.ts` that behaves
 * as Stripe's test cards do.
 *
 * ## A component on a port
 *
 * The fields are a **view**, not a call: what is typed stays inside them, and the provider reads it
 * from there when the card is taken. So the port carries `CardFields` — Stripe's `CardField`,
 * styled to the mock (43) — beside its verbs, and the fake carries a field a suite can type a test
 * number into. What either tells the screen is only whether the entry is complete.
 *
 * ## Three verbs, and none of them rejects
 *
 * - **`phoneWallet`** — the phone's own wallet, when it can pay with it: Google Pay on Android when
 *   Google says it is ready; **Apple Pay on an iPhone only once a merchant identifier exists**, which
 *   needs the Apple Developer membership (open items O4, O6). Until then an iPhone offers a card.
 * - **`takeCard`** — turn what the fields hold into a reference the setup is confirmed with, while
 *   they are still on screen (Stripe reads the entry out of the mounted view, and the card details
 *   step collapses once saved). A reference, not a card: nothing above this file can read it.
 * - **`confirmSetup`** — ask the bank, with the setup's secret: Stripe's SDK confirms, draws the
 *   bank's check when the bank wants one, and answers. **A bank that asks nothing answers at once**,
 *   which is what lets step 4 tick itself. The answer is one of four words, never an error: the
 *   player closing the check is `cancelled`, a refusal is `declined`, anything else `failed`.
 *
 * And a fourth, for the one payment that ever needs the player (#555; the mechanics §12.2):
 *
 * - **`confirmPayment`** — a share refused when its game filled, confirmed in the app on **the
 *   club's account**, where every charge is made (a direct charge; ADR-0189 §4). With the card on
 *   file, the bank's check is drawn over the payment it refused — Stripe's own recovery for an
 *   off-session payment that wanted its customer: the payment is confirmed again with the card
 *   it last tried (`lastPaymentError`). With another card, the fields' entry pays it instead. The
 *   same four words, `confirmed` for `saved`.
 *
 * ## A key that is not Stripe's
 *
 * The server answers the key the fields open with (`POST …/setup`). A laptop run's provider is the
 * backend's in-process fake, whose key is not Stripe's and whose setups confirm themselves as they
 * are read — so there is nothing on the phone to confirm against, and a real SDK handed that key
 * would fail at the network. **Any key that is not a Stripe key is that provider**: the fields still
 * take a card, `takeCard` answers without calling anybody, and the bank answers `saved` at once. It
 * is the key that decides, never the environment's name — a laptop configured with Stripe's test
 * keys talks to Stripe.
 *
 * ## The way back from the bank's own app
 *
 * A bank that checks in its own app returns to Rakieta through the app's scheme, and on iOS Stripe's
 * SDK needs that address handed to it. The listener lives exactly as long as a confirmation, here,
 * so nothing else in the app hears of it — and `+native-intent` ignores an address it does not know,
 * so the screen underneath stays where it was.
 */

import {
  CardField,
  PlatformPay,
  confirmPayment as confirmStripePayment,
  confirmPlatformPaySetupIntent,
  confirmSetupIntent,
  createPaymentMethod,
  handleURLCallback,
  initStripe,
  isPlatformPaySupported,
  retrievePaymentIntent,
} from '@stripe/stripe-react-native';
import { useEffect, useLayoutEffect, type ComponentType } from 'react';
import { Linking, Platform, StyleSheet } from 'react-native';
import TextInputState from 'react-native/Libraries/Components/TextInput/TextInputState';

import { APPLE_PAY_MERCHANT } from '@/shared/config/applePay';
import { APP_SCHEME } from '@/shared/config/appLinks';
import { theme } from '@/shared/ui/theme';

/** The phone's own wallet — the one of the two this phone has (the mechanics §12.4, Q82). */
export type PhoneWallet = 'APPLE_PAY' | 'GOOGLE_PAY';

/** What the fields say about what has been typed — never the number. */
export interface CardEntry {
  /** A number, an expiry and a CVC that pass the provider's own checks. */
  readonly complete: boolean;
}

export interface CardFieldsProps {
  readonly onChange: (entry: CardEntry) => void;
  /** The grey words in the empty fields — the caller's copy. */
  readonly placeholders: { readonly number: string; readonly expiry: string; readonly cvc: string };
  readonly accessibilityLabel: string;
}

/** A card taken out of the fields — the provider's reference to it, opaque above this file. */
export interface TakenCard {
  readonly reference: string | null;
}

export type CardTaking =
  | { readonly kind: 'taken'; readonly card: TakenCard }
  /** The provider could not take what was typed — or could not be reached. Nothing was saved. */
  | { readonly kind: 'refused' };

export type ConfirmWith =
  | { readonly kind: 'card'; readonly card: TakenCard }
  | {
      readonly kind: 'wallet';
      readonly wallet: PhoneWallet;
      /** The line the wallet's sheet shows above its button — the caller's copy. */
      readonly sheetLabel: string;
    };

/**
 * What the bank said.
 *
 * - `saved` — the setup is confirmed; the server's confirmation reads it as it stands.
 * - `cancelled` — the player closed the bank's check, or the wallet's sheet. Nothing is saved.
 * - `declined` — the bank refused the card. The same setup can try another.
 * - `failed` — anything else, the network among it.
 */
export type BankAnswer = 'saved' | 'cancelled' | 'declined' | 'failed';

export interface ConfirmSetup {
  readonly publishableKey: string;
  /** The setup's secret — the server's answer to the terms, never kept past this call. */
  readonly clientSecret: string;
  readonly with: ConfirmWith;
}

/** What the bank said to a payment confirmed in the app — `BankAnswer`'s four, for a payment. */
export type PaymentAnswer = 'confirmed' | 'cancelled' | 'declined' | 'failed';

export interface ConfirmPayment {
  readonly publishableKey: string;
  /** The club's account — a direct charge is confirmed on the seller's account. */
  readonly accountId: string;
  /** The payment's secret — asked of the server for this press, and never kept past this call. */
  readonly clientSecret: string;
  /**
   * `onFile` — the card the payment was refused on, through the bank's check; `typed` — another card,
   * in the fields on screen now.
   */
  readonly with: 'onFile' | 'typed';
}

/**
 * What the app may ask of the payment provider on the phone.
 *
 * Screens depend on this interface; `devicePayments` is the one implementation that talks to
 * Stripe, and a test substitutes `fakePayments()` from `src/test-support/platform.ts`.
 */
export interface PaymentsPort {
  /** The provider's card fields — number, expiry, CVC. Drawn only after `prepare` said yes. */
  readonly CardFields: ComponentType<CardFieldsProps>;
  /**
   * Start the provider with the setup's key before any of its fields are drawn. Android's native
   * field reads the SDK's configuration when it mounts, and only `initStripe` sets it — a field
   * mounted first fails with *PaymentConfiguration was not initialized*. `false` when it cannot
   * start; it never rejects.
   */
  readonly prepare: (publishableKey: string) => Promise<boolean>;
  /** The phone's own wallet, or `null` when it cannot pay with one. */
  readonly phoneWallet: () => Promise<PhoneWallet | null>;
  /** Take the card the fields hold, while they are on screen. */
  readonly takeCard: (publishableKey: string) => Promise<CardTaking>;
  /** Ask the bank to save it. */
  readonly confirmSetup: (ask: ConfirmSetup) => Promise<BankAnswer>;
  /** Confirm a refused share on the club's account. */
  readonly confirmPayment: (ask: ConfirmPayment) => Promise<PaymentAnswer>;
}

/** Poland, in złoty — where every club charging through Rakieta sells today. */
const MERCHANT_COUNTRY = 'PL';
const CURRENCY = 'PLN';

/** A Stripe publishable key, test or live. Anything else is a provider with no phone half. */
export function isStripeKey(publishableKey: string): boolean {
  return /^pk_(test|live)_/.test(publishableKey);
}

/** The shape every Stripe answer shares: an error, or not. */
interface StripeOutcome {
  readonly error?: {
    readonly code: string;
    readonly declineCode?: string;
    readonly stripeErrorCode?: string;
    readonly type?: string;
  };
}

/** One of the four words, from what Stripe's SDK answered. */
export function bankAnswerOf({ error }: StripeOutcome): BankAnswer {
  if (error === undefined) return 'saved';
  if (error.code === 'Canceled') return 'cancelled';
  if (
    error.declineCode !== undefined ||
    error.stripeErrorCode === 'card_declined' ||
    error.type === 'card_error'
  ) {
    return 'declined';
  }
  return 'failed';
}

/** A payment's four words, from what Stripe's SDK answered — `bankAnswerOf`'s, for a payment. */
export function paymentAnswerOf(outcome: StripeOutcome): PaymentAnswer {
  const said = bankAnswerOf(outcome);
  return said === 'saved' ? 'confirmed' : said;
}

/**
 * The key and the account Stripe was last started with — started once per pair, not once per
 * press. A setup is confirmed on the platform (no account); a payment on the club's.
 */
let startedWith: string | undefined;

async function start(publishableKey: string, accountId?: string): Promise<void> {
  const pair = `${publishableKey}|${accountId ?? ''}`;
  if (startedWith === pair) return;
  await initStripe({
    publishableKey,
    urlScheme: APP_SCHEME,
    ...(accountId === undefined ? {} : { stripeAccountId: accountId }),
    ...(APPLE_PAY_MERCHANT === null ? {} : { merchantIdentifier: APPLE_PAY_MERCHANT }),
  });
  startedWith = pair;
}

/** Hand Stripe the bank app's way back for as long as `work` runs. */
async function whileTheBankMayReturn<T>(work: () => Promise<T>): Promise<T> {
  const listening = Linking.addEventListener('url', ({ url }) => {
    void handleURLCallback(url);
  });
  try {
    return await work();
  } finally {
    listening.remove();
  }
}

/**
 * The native input the card field registered when it took focus, or `null`. Stripe's field tells
 * React Native that it is focused, and a focus it registered is what its unmount checks.
 */
let focusedCardField: unknown = null;

/** The card field took focus: remember which native input it is. */
export function rememberCardFocus() {
  focusedCardField = TextInputState.currentlyFocusedInput();
}

/**
 * Forget the card field's focus before its view goes, without a native blur.
 *
 * Stripe's field calls `blur()` on its native view when it unmounts while it still counts as the
 * focused input — and on iOS, under the New Architecture, that call reaches a view that is no longer
 * there and traps (#552). `Keyboard.dismiss()` would send a native blur too, so it is not used here.
 * `blurInput` only clears React Native's record, so the unmount finds nothing to blur. The keyboard
 * goes with the view.
 */
export function releaseCardFocus() {
  const current = TextInputState.currentlyFocusedInput();
  if (current !== null && current === focusedCardField) TextInputState.blurInput(current);
  focusedCardField = null;
}

function StripeCardFields({ onChange, placeholders, accessibilityLabel }: CardFieldsProps) {
  // Parent cleanups run before the field's own unmount, so the record is cleared first.
  useLayoutEffect(() => releaseCardFocus, []);
  // Android's field cannot tell the app what is typed: under the New Architecture it has no event
  // dispatcher (`getNativeModule(UIManagerModule)` is not allowed), so its change events never
  // arrive and "complete" would stay false, keeping Save disabled. Stripe still checks the card when
  // Save takes it, and refuses an incomplete one with the usual sentence — so Android counts the
  // fields as ready. iOS's field reports its changes and keeps the check.
  useEffect(() => {
    if (Platform.OS === 'android') onChange({ complete: true });
  }, [onChange]);
  return (
    <CardField
      onFocus={rememberCardFocus}
      postalCodeEnabled={false}
      placeholders={{
        number: placeholders.number,
        expiration: placeholders.expiry,
        cvc: placeholders.cvc,
      }}
      cardStyle={CARD_STYLE}
      style={s.fields}
      accessibilityLabel={accessibilityLabel}
      onCardChange={(card) => onChange({ complete: card.complete })}
    />
  );
}

export const devicePayments: PaymentsPort = {
  CardFields: StripeCardFields,

  async prepare(publishableKey) {
    // The laptop's provider has no Stripe key, and its fields take no real card — but Android's
    // native field still reads the SDK's configuration when it mounts, so the placeholder starts it
    // too (the Change → Continue crash, #552). iOS's field does not, and is left as it was.
    if (!isStripeKey(publishableKey) && Platform.OS !== 'android') return true;
    try {
      await start(publishableKey);
      return true;
    } catch {
      return false;
    }
  },

  async phoneWallet() {
    try {
      if (Platform.OS === 'ios') {
        if (APPLE_PAY_MERCHANT === null) return null;
        return (await isPlatformPaySupported()) ? 'APPLE_PAY' : null;
      }
      // Android's Google Pay check builds the SDK's launcher, which reads the configuration that only
      // `initStripe` sets; asked before the provider has started, it throws and the app closes (the
      // Change button on the Payments screen, #552). Until a setup has started Stripe, Google Pay is
      // not offered — and the next visit, which asks after a start, offers it.
      if (startedWith === undefined) return null;
      return (await isPlatformPaySupported()) ? 'GOOGLE_PAY' : null;
    } catch {
      return null;
    }
  },

  async takeCard(publishableKey) {
    if (!isStripeKey(publishableKey)) return { kind: 'taken', card: { reference: null } };
    // The step closes once this answers, and its field unmounts; release the focus before that.
    releaseCardFocus();
    try {
      await start(publishableKey);
      const { paymentMethod, error } = await createPaymentMethod({ paymentMethodType: 'Card' });
      if (error !== undefined || paymentMethod === undefined) return { kind: 'refused' };
      return { kind: 'taken', card: { reference: paymentMethod.id } };
    } catch {
      return { kind: 'refused' };
    }
  },

  async confirmSetup({ publishableKey, clientSecret, with: via }) {
    if (!isStripeKey(publishableKey)) return 'saved';
    try {
      await start(publishableKey);
      return await whileTheBankMayReturn(async () => {
        if (via.kind === 'wallet') {
          return bankAnswerOf(
            await confirmPlatformPaySetupIntent(clientSecret, {
              googlePay: {
                testEnv: publishableKey.startsWith('pk_test_'),
                merchantCountryCode: MERCHANT_COUNTRY,
                currencyCode: CURRENCY,
                merchantName: via.sheetLabel,
              },
              applePay: {
                merchantCountryCode: MERCHANT_COUNTRY,
                currencyCode: CURRENCY,
                cartItems: [
                  {
                    paymentType: PlatformPay.PaymentType.Immediate,
                    label: via.sheetLabel,
                    amount: '0.00',
                    isPending: true,
                  },
                ],
              },
            }),
          );
        }
        const reference = via.card.reference;
        if (reference === null) return 'failed';
        return bankAnswerOf(
          await confirmSetupIntent(clientSecret, {
            paymentMethodType: 'Card',
            paymentMethodData: { paymentMethodId: reference },
          }),
        );
      });
    } catch {
      return 'failed';
    }
  },

  async confirmPayment({ publishableKey, accountId, clientSecret, with: via }) {
    if (!isStripeKey(publishableKey)) return 'confirmed';
    try {
      await start(publishableKey, accountId);
      return await whileTheBankMayReturn(async () => {
        if (via === 'typed') {
          return paymentAnswerOf(
            await confirmStripePayment(clientSecret, { paymentMethodType: 'Card' }),
          );
        }
        // The card it was refused on: off-session, Stripe leaves it on the payment's last error.
        const { paymentIntent, error } = await retrievePaymentIntent(clientSecret);
        if (error !== undefined || paymentIntent === undefined) return 'failed';
        const onFile =
          paymentIntent.lastPaymentError?.paymentMethod?.id ?? paymentIntent.paymentMethodId;
        if (onFile === undefined || onFile === null) return 'failed';
        return paymentAnswerOf(
          await confirmStripePayment(clientSecret, {
            paymentMethodType: 'Card',
            paymentMethodData: { paymentMethodId: onFile },
          }),
        );
      });
    } catch {
      return 'failed';
    }
  },
};

/**
 * Stripe's fields, drawn as the mock draws a field (43): the text field's surface, border and
 * radius, the number in the mono face. The native view takes plain values, so these are the
 * theme's, read once.
 */
const CARD_STYLE = {
  backgroundColor: theme.color.surface,
  borderColor: theme.color.line,
  borderWidth: 1,
  borderRadius: theme.radius.btn,
  textColor: theme.color.ink,
  placeholderColor: theme.color.muted,
  cursorColor: theme.color.ink,
  textErrorColor: theme.color.red,
  fontFamily: theme.font.mono[500],
  fontSize: theme.num.s.fontSize,
} as const;

const s = StyleSheet.create({
  fields: { width: '100%', height: theme.size.payments.cardFields },
});
