/**
 * **A player's payment method, in the words the screens use** — the saved method, the setup that
 * saves one, and the reason a removal is refused
 * ([#552](https://github.com/Raketa02/Raketa/issues/552); the mechanics §12.4, §12.5).
 *
 * The wallet union is the wire's own, held equal to the generated one in
 * `mappers/wireVocabulary.ts`, because a copy table is keyed by it — the method card's badge and the
 * row's line both name the wallet.
 */

/** The phone's own wallet a card was saved through — Apple Pay on an iPhone, Google Pay on Android. */
export type Wallet = 'APPLE_PAY' | 'GOOGLE_PAY';

/**
 * How a player can choose to pay, as step 1's chips offer it (the mechanics §12.4): a card typed
 * into Stripe's fields, BLIK, or the phone's wallet. BLIK is offered and cannot continue yet.
 */
export type PayWith = 'CARD' | 'BLIK' | Wallet;

/** Whether this way of paying is one of the two wallets. */
export function isWallet(payWith: PayWith): payWith is Wallet {
  return payWith === 'APPLE_PAY' || payWith === 'GOOGLE_PAY';
}

/** The method the clubs charge — never the number, only what the provider tells Rakieta of it. */
export interface SavedMethod {
  /** The card network as the provider names it, lower case — an open set (`visa`, `mastercard`…). */
  readonly brand: string;
  readonly lastFour: string;
  /** The wallet it was saved through, or `null` for a card typed in. */
  readonly wallet: Wallet | null;
}

/** What `GET …/payment-methods/current` answers: the method, and whether its terms must be asked again. */
export interface PaymentMethodStanding {
  /** `null` is *Not set up* — state A. */
  readonly method: SavedMethod | null;
  /**
   * The bank moved the card to another brand, and it cannot be charged until the terms are
   * accepted again (the mechanics §12.5). Always `false` with no method.
   */
  readonly termsNeeded: boolean;
}

/** A setup opened at the server: what the phone opens the provider's fields with. Never the secret. */
export interface SetupOpened {
  /** Not a secret — it collects details and can charge nothing. */
  readonly publishableKey: string;
  /** The terms in force. The client shows its own words only when they are these. */
  readonly termsVersion: string;
}

/** Why a removal was refused (Q83): what still needs the method. */
export interface MethodInUse {
  readonly liveYeses: number;
  readonly upcomingGames: number;
}
