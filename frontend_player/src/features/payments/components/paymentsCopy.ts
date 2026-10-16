/**
 * **Every sentence You › Payments says** — the row, the four steps, the method card, and the terms
 * ([#552](https://github.com/Raketa02/Raketa/issues/552); the screens A7, A7.3; mocks 40–47).
 *
 * ## The terms are evidence, not copy
 *
 * `PAYMENT_TERMS` is what a player agrees to before anything is saved (the mechanics §12.5), and
 * the backend records **the version** beside the moment and the address — never the words, which
 * are the client's (`payments/domain/terms.py`, #536). So **changing a word below is a new version,
 * not an edit**: bump the identifier with the backend's, keep the retired words, and leave every
 * acceptance already recorded pointing at what it was shown: a silent re-word turns every
 * recorded acceptance into a record of something nobody agreed to. The version is the day the
 * words were settled.
 *
 * They are §12.5's words (Q113) less its first sentence — *Your card is saved* is not yet true on
 * the step that shows them: who holds the share and when, the card check on a game far ahead, the
 * take at the club's cut-off, what leaving costs before and after it, and that a game still short at
 * the cut-off is called off with nothing taken. The wording is reviewed by a lawyer before launch
 * (open item O3) — the clause after the cut-off above all — and ships under a new version.
 *
 * ## The wallet's name, in one place
 *
 * *Google Pay* and *Apple Pay* are chips on step 1, the row's whole line for a wallet's card, and
 * the badge on the method card — one table keyed by the wire's own union, so a third wallet does
 * not compile without its words.
 */

import { counted } from '@/shared/formatting/counted';
import { sentenceList } from '@/shared/formatting/sentenceList';

import type { SetupFailure } from '../domain/setupRefusal';
import {
  SETUP_STEP_ORDER,
  type SetupStep,
  type SetupStepName,
  type SetupStepState,
} from '../domain/setupSteps';
import type {
  MethodInUse,
  PaymentMethodStanding,
  PayWith,
  SavedMethod,
  Wallet,
} from '../domain/vocabulary';

/** The screen's and the row's title. */
export const PAYMENTS_TITLE = 'Payments';

/**
 * The identifier the backend holds in force and records with an acceptance (#536). Sent back with
 * *Accept and continue*; a phone showing any other words is refused (`payment_terms_outdated`).
 * Since #637 it is Q113's, and a player who accepted an earlier version is asked again.
 */
export const PAYMENT_TERMS_VERSION = '2026-10-10';

/** One run of the terms' text — bold where the mock sets it bold. */
export interface TermsRun {
  readonly text: string;
  readonly strong?: boolean;
}

/** The terms, version `2026-10-10` — the mechanics §12.5 (Q113). Frozen: see the module note. */
export const PAYMENT_TERMS: readonly TermsRun[] = [
  { text: 'When a game you said yes to fills, ' },
  { text: 'the club it is played at', strong: true },
  {
    text:
      ' holds your share on your card — the court’s price divided by the players. If that hold ' +
      'would not last until the club’s cut-off, your card is checked when the game fills (your ' +
      'share held for a moment and let go), and your share is held four days before the cut-off. ' +
      'Your share is taken at the club’s cut-off. Leave before the cut-off and nothing is taken. ' +
      'After the cut-off your seat is offered to others; if someone takes it, you get your share ' +
      'back less what was kept on your payment, and you see the exact sum before you leave. If a ' +
      'game is still missing a player at the cut-off, it is called off and nothing is taken.',
  },
];

/**
 * **The runs earlier versions showed, by version** — kept, as the module note asks, so an acceptance
 * recorded under one still points at what it was shown, bold where it was. Never shown again.
 */
export const RETIRED_PAYMENT_TERMS: Readonly<Record<string, readonly TermsRun[]>> = {
  '2026-09-29': [
    { text: 'When a game you said yes to fills, ' },
    { text: 'the club it is played at', strong: true },
    {
      text:
        ' charges your share at once — the court’s price divided by the players. Free to leave ' +
        'until the club’s cut-off — refunded minus the card fee; after it, refunded when someone ' +
        'takes your seat. A game still missing a player at the cut-off is called off, and everyone ' +
        'gets everything back.',
    },
  ],
};

/** The terms as one string — their spoken form, and what a suite reads. */
export const PAYMENT_TERMS_TEXT = PAYMENT_TERMS.map((run) => run.text).join('');

/** How each way of paying is named, on its chip and wherever it is named again. */
export const PAY_WITH_NAME: Readonly<Record<PayWith, string>> = {
  CARD: 'Card',
  BLIK: 'BLIK',
  APPLE_PAY: 'Apple Pay',
  GOOGLE_PAY: 'Google Pay',
};

const WALLET_BADGE: Readonly<Record<Wallet, string>> = {
  GOOGLE_PAY: 'GPay',
  APPLE_PAY: 'Apple Pay',
};

/** The networks with a badge of their own. The set is open, and the rest are a plain card (#536). */
const BRAND_BADGE: Readonly<Record<string, string>> = {
  visa: 'VISA',
  mastercard: 'MC',
  amex: 'AMEX',
};

export const STEP_TITLE: Readonly<Record<SetupStepName, string>> = {
  choose: 'Choose how you pay',
  card: 'Card details',
  terms: 'Accept the terms',
  bank: 'Confirm with your bank',
};

const STEP_STATE_SPOKEN: Readonly<Record<SetupStepState, string>> = {
  open: 'now',
  done: 'done',
  skipped: 'not needed',
  waiting: 'to come',
};

export const PAYMENTS_COPY = {
  row: {
    notSetUp: 'Not set up',
    /** After the method's own line, when the bank moved its card to another brand. */
    termsAgain: 'accept the terms again',
  },
  loading: 'Reading your payment method…',
  readAgain: 'Try again',
  blikNotice: 'BLIK launches when Stripe confirms saved BLIK — pick a card or wallet for now.',
  continue: 'Continue',
  opening: 'Opening…',
  saveTheCard: 'Save the card',
  saving: 'Saving…',
  cardFields: {
    label: 'Card number, expiry date and security code',
    placeholders: { number: '1234 1234 1234 1234', expiry: 'MM/YY', cvc: 'CVC' },
  },
  accept: 'Accept and continue',
  accepting: 'Accepting…',
  bankLine:
    'One-time 3-D Secure check — it lets the club hold and take your share later without you present.',
  askTheBank: 'Open the bank app · confirm',
  asking: 'Waiting for your bank…',
  /** The merchant the wallet's own sheet names — Raketa keeps the card; the clubs hold and take it. */
  walletSheet: 'Raketa',
  chooseAgain: 'Change how you pay',
  /** What the open step says went wrong — every failure but a refusal the server named itself. */
  failures: {
    CARD_REFUSED: 'Stripe couldn’t take this card. Check the number, the date and the code.',
    PROVIDER_NOT_STARTED: 'Card payments couldn’t start on this phone. Try again in a moment.',
    BANK_CLOSED: 'The check was closed before your bank finished, so nothing is saved. Try again.',
    CARD_DECLINED: 'Your bank declined this card, so nothing is saved. Try another one.',
    BANK_FAILED: 'We couldn’t hear back from your bank. Try again.',
    BANK_NOT_DONE: 'Your bank hasn’t finished its check yet. Try again in a moment.',
    SETUP_GONE: 'That setup expired. Start again from the first step.',
    TERMS_OUTDATED: 'These terms have changed. Update Raketa to read the new ones first.',
  } satisfies Readonly<Record<Exclude<SetupFailure['kind'], 'SAY_SO'>, string>>,
  /** A refused write, by its code — anything else is the recovery's own sentence. */
  refusals: {
    payment_setups_exhausted: 'You’ve started five setups today. Try again tomorrow.',
    payments_unavailable: 'Payments can’t be reached right now. Try again in a moment.',
    adult_attestation_missing: 'Finish Start playing before you save a way to pay.',
  } as Readonly<Record<string, string>>,
  method: {
    /** The method card's line (the screens A7.3, Q113). */
    heldAndTaken: 'Held when a game fills · taken by the club at its cut-off',
    change: 'Change',
    remove: 'Remove this method',
    removing: 'Removing…',
    keep: 'Keep this one',
    termsAgainTitle: 'Accept the terms again',
    /**
     * Either reason the read's `terms_needed` names, which it does not tell apart (#637): words no
     * longer in force, or a card its bank moved to another brand.
     */
    termsAgainLine:
      'Clubs can’t hold your share on this card until you accept the terms in force — they changed, or your bank moved the card to another network.',
    termsAgain: 'Accept the terms',
  },
  /**
   * **The setup as a sheet over the deck** — a first yes with nothing saved (the mechanics §6.1;
   * the screens A2.4). The yes lands when the method is saved, or is dropped when the sheet closes.
   */
  setupSheet: {
    title: 'Before your first yes',
    close: 'Close the payment setup — your yes is not sent',
    line: 'Save how you pay. Nothing is held until a game you said yes to fills, and nothing is taken before the club’s cut-off.',
  },
  /** *RECEIPTS* (mock 49) — the club named as the seller, newest first. */
  receipts: {
    title: 'Receipts',
    empty: 'Nothing yet — charges and refunds land here, with the club named as the seller.',
    /** Under the rows — no BLIK line while BLIK isn't offered (the screens A7.3, Q113). */
    footer: 'Refunds can take up to two weeks to reach your card.',
    today: 'Today',
    tomorrow: 'Tomorrow',
    yesterday: 'Yesterday',
    unknownClub: 'A club',
    /** *−40 zł · paid*, *+38,24 zł · refunded*, *40 zł held · released* (the screens A7.3, #644). */
    paid: 'paid',
    refunded: 'refunded',
    held: 'held',
    released: 'released',
    /** Under a refund: *1,76 zł kept on your payment* — the exact fee, never an estimate. */
    keptOnYourPayment: 'kept on your payment',
    /** Under a hold let go: *Released 28 Sep*, the day it was, as a bank app dates the hold. */
    releasedOn: 'Released',
  },
} as const;

/** The card's own line — *Card •••• 4312*. */
export function cardLine(method: SavedMethod): string {
  return `Card •••• ${method.lastFour}`;
}

/** The row's line: the wallet by name, a typed card by its last four, or *Not set up*. */
export function paymentsRowLine({ method, termsNeeded }: PaymentMethodStanding): string {
  if (method === null) return PAYMENTS_COPY.row.notSetUp;
  const named = method.wallet === null ? cardLine(method) : PAY_WITH_NAME[method.wallet];
  return termsNeeded ? `${named} · ${PAYMENTS_COPY.row.termsAgain}` : named;
}

/** The method card's square: the wallet's mark, the network's, or a plain *CARD*. */
export function methodBadge(method: SavedMethod): string {
  if (method.wallet !== null) return WALLET_BADGE[method.wallet];
  return BRAND_BADGE[method.brand] ?? 'CARD';
}

/** The method card's spoken name — the badge's words say the brand, which a square cannot. */
export function methodCardLabel(method: SavedMethod): string {
  const through = method.wallet === null ? '' : `, in ${PAY_WITH_NAME[method.wallet]}`;
  return `${cardLine(method)}${through}. ${PAYMENTS_COPY.method.heldAndTaken}`;
}

/** *Changing* — the line over the checklist, saying the old method still pays until then. */
export function keepsWorkingLine(method: SavedMethod): string {
  return `${cardLine(method)} keeps working until the new one is saved.`;
}

/** Step 2's right-hand words for a wallet: the wallet holds the card. */
export function inTheWallet(wallet: Wallet): string {
  return `In ${PAY_WITH_NAME[wallet]}`;
}

/** A step's spoken name: its number of the four, its title, where it stands, and its answer. */
export function stepLabel({ number, name, state }: SetupStep, aside: string | undefined): string {
  const answered = aside === undefined ? '' : `, ${aside}`;
  return `Step ${number} of ${SETUP_STEP_ORDER.length}, ${STEP_TITLE[name]}, ${STEP_STATE_SPOKEN[state]}${answered}`;
}

/** Why *Remove this method* was refused (Q83) — what still needs it, counted when the server said. */
export function inUseLine(counts: MethodInUse | null): string {
  const needs: string[] = [];
  if (counts !== null && counts.liveYeses > 0) {
    needs.push(counted(counts.liveYeses, 'live yes', 'live yeses'));
  }
  if (counts !== null && counts.upcomingGames > 0) {
    needs.push(counted(counts.upcomingGames, 'booked game ahead', 'booked games ahead'));
  }
  if (needs.length === 0) {
    return 'It can’t be removed while it still pays for a live yes or a booked game.';
  }
  return `It can’t be removed while it still pays for ${sentenceList(needs)}.`;
}
