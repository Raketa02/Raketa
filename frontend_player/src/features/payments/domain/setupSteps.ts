/**
 * **The payment setup's four steps, as a machine** — which step is open, which are finished, and
 * what each press moves ([#552](https://github.com/Raketa02/Raketa/issues/552); the screens A7.3;
 * the mechanics §12.5).
 *
 * ## The order is Q82's, and the contract's
 *
 * 1. **Choose how you pay** — a card, BLIK, or the phone's wallet. BLIK cannot continue yet.
 * 2. **Card details** — Stripe's own fields. **A wallet skips it**: the wallet holds the card.
 * 3. **Accept the terms** — before anything is saved, which is why it is third and not last as
 *    the mocks drew it: the setup's secret is the server's answer to the terms, so the bank cannot
 *    be asked before them.
 * 4. **Confirm with your bank** — this step saves; it has no *done*, because a saved method is
 *    state B and the checklist is gone.
 *
 * ## What survives a step going back
 *
 * The terms are accepted **for the setup**, not for a card: when the bank refuses a card the same
 * setup can try another (`payment_method_declined`), so the card details open again and the next
 * card goes straight to the bank. Going back to the choice forgets the card — its fields are gone
 * with its step — and keeps the terms. Only a setup gone at the server starts everything over.
 *
 * Every event outside the step it belongs to answers the progress unchanged — the same object — so
 * a late answer arriving after the player moved on moves nothing.
 */

import { isWallet, type PayWith, type Wallet } from './vocabulary';

export type SetupStepName = 'choose' | 'card' | 'terms' | 'bank';

/** The four steps, in the order they are drawn and walked. */
export const SETUP_STEP_ORDER: readonly SetupStepName[] = ['choose', 'card', 'terms', 'bank'];

/**
 * How a step is drawn: the one step being worked on, one finished (a green tick), one a wallet made
 * unnecessary, or one still ahead (grey).
 */
export type SetupStepState = 'open' | 'done' | 'skipped' | 'waiting';

export interface SetupStep {
  readonly name: SetupStepName;
  /** 1 to 4 — the number in the step's circle, the same whatever was skipped. */
  readonly number: number;
  readonly state: SetupStepState;
}

export interface SetupProgress {
  /** The step being worked on. */
  readonly open: SetupStepName;
  /** The chip selected on step 1, or none yet. */
  readonly chosen: PayWith | null;
  /** Stripe's fields have turned what was typed into something a setup can be confirmed with. */
  readonly cardSaved: boolean;
  /** The terms are accepted for this setup, and its secret is in hand. */
  readonly termsAccepted: boolean;
}

export const SETUP_START: SetupProgress = {
  open: 'choose',
  chosen: null,
  cardSaved: false,
  termsAccepted: false,
};

export type SetupEvent =
  /** A chip on step 1. */
  | { readonly type: 'chose'; readonly payWith: PayWith }
  /** *Continue* on step 1. */
  | { readonly type: 'continued' }
  /** *Save the card* on step 2, answered. */
  | { readonly type: 'cardSaved' }
  /** *Accept and continue* on step 3, answered with the setup's secret. */
  | { readonly type: 'termsAccepted' }
  /** The bank refused the card (or the wallet's card) on step 4. */
  | { readonly type: 'declined' }
  /** A finished step 1 pressed — the player changes how they pay. */
  | { readonly type: 'reopened' }
  /** The setup is gone at the server — never started, or cancelled there. */
  | { readonly type: 'startedOver' };

/**
 * Step 1's chips: a card, BLIK, and **the phone's own wallet when it has one** — Apple Pay on an
 * iPhone, Google Pay on Android, never the other one (§12.4, Q82).
 */
export function waysToPay(phoneWallet: Wallet | null): readonly PayWith[] {
  return phoneWallet === null ? ['CARD', 'BLIK'] : ['CARD', 'BLIK', phoneWallet];
}

/**
 * Whether the words this phone shows are the terms in force. Unknown until a setup names the version
 * in force — and then *Accept* agrees only to those words.
 */
export function wordsInForce(shown: string, inForce: string | null): boolean {
  return inForce === null || inForce === shown;
}

/** Whether step 1's answer is one of the wallets. */
function choseAWallet(progress: SetupProgress): boolean {
  return progress.chosen !== null && isWallet(progress.chosen);
}

/** Whether *Continue* may be pressed: a card or a wallet. BLIK launches when Stripe confirms saved BLIK (§12.4). */
export function canContinue(chosen: PayWith | null): boolean {
  return chosen !== null && chosen !== 'BLIK';
}

/** The step after the card details — the terms, unless they are already accepted for this setup. */
function afterTheCard(progress: SetupProgress): SetupStepName {
  return progress.termsAccepted ? 'bank' : 'terms';
}

export function advance(progress: SetupProgress, event: SetupEvent): SetupProgress {
  switch (event.type) {
    case 'chose':
      return progress.open === 'choose' ? { ...progress, chosen: event.payWith } : progress;

    case 'continued': {
      const { chosen } = progress;
      if (progress.open !== 'choose' || chosen === null || !canContinue(chosen)) return progress;
      return { ...progress, open: isWallet(chosen) ? afterTheCard(progress) : 'card' };
    }

    case 'cardSaved':
      return progress.open === 'card'
        ? { ...progress, cardSaved: true, open: afterTheCard(progress) }
        : progress;

    case 'termsAccepted':
      return progress.open === 'terms'
        ? { ...progress, termsAccepted: true, open: 'bank' }
        : progress;

    case 'declined': {
      if (progress.open !== 'bank') return progress;
      return choseAWallet(progress)
        ? { ...progress, open: 'choose' }
        : { ...progress, open: 'card', cardSaved: false };
    }

    case 'reopened':
      return progress.open === 'choose'
        ? progress
        : { ...progress, open: 'choose', cardSaved: false };

    case 'startedOver':
      return { ...SETUP_START, chosen: progress.chosen };
  }
}

/** The four steps as the checklist draws them. */
export function setupSteps(progress: SetupProgress): readonly SetupStep[] {
  return SETUP_STEP_ORDER.map((name, index) => ({
    name,
    number: index + 1,
    state: stateOf(name, progress),
  }));
}

function stateOf(name: SetupStepName, progress: SetupProgress): SetupStepState {
  if (progress.open === name) return 'open';
  switch (name) {
    case 'choose':
      return 'done';
    case 'card':
      // Skipped only once the wallet is the answer; while the player is still choosing, the list
      // does not change under the chips.
      if (choseAWallet(progress) && progress.open !== 'choose') return 'skipped';
      return progress.cardSaved ? 'done' : 'waiting';
    case 'terms':
      return progress.termsAccepted ? 'done' : 'waiting';
    case 'bank':
      return 'waiting';
  }
}
