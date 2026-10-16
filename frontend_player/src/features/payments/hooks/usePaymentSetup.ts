/**
 * **The four-step setup, run** — the machine in `domain/setupSteps`, the provider's phone half
 * behind `usePayments()`, and the three writes the server takes in order
 * ([#552](https://github.com/Raketa02/Raketa/issues/552); the mechanics §12.5; the screens A7.3).
 *
 * | Press | What happens |
 * | --- | --- |
 * | *Continue* (step 1) | `POST …/setup` — once per visit: the key the fields open with, and the terms in force |
 * | *Save the card* (step 2) | the provider takes the card out of its fields, while they are on screen |
 * | *Accept and continue* (step 3) | `POST …/terms` with the version of the words shown — answered with the setup's secret |
 * | step 4, **by itself** | the bank is asked with the secret; `POST …/confirmation` saves what it said |
 *
 * ## Step 4 asks the bank the moment it opens
 *
 * The screens say it *ticks by itself when the bank asks nothing*, and that is only possible if
 * nobody has to press anything: arriving at step 4 — from the terms, or from a second card after a
 * decline — asks the bank at once. A bank with no check answers straight away and the method is
 * saved; one with a check draws it over the screen (Stripe's SDK does). **The button on the step is
 * for asking again**: after the player closed the check, after a failure, or while the server says
 * the check is not done.
 *
 * ## One setup per visit
 *
 * The server allows five a day, and a second one replaces the first at the provider. So the setup
 * opened by the first *Continue* is kept for as long as the screen is — a changed mind on step 1, a
 * refused card, a closed check all reuse it — and only the server saying it is gone opens another.
 * The secret is kept exactly as long: in a ref, never in state a render could print, and gone with
 * the screen.
 *
 * ## The writes are made online or not at all
 *
 * The app's mutations pause while offline and resume on reconnect. These three do not
 * (`networkMode: 'always'`): each is one step of a flow the player is standing in, with Stripe's
 * native half between them, and a press that went nowhere should say so now — a busy button that
 * resumes a setup some minutes later, after the player has given up, is worse than a sentence.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';

import type { AppError } from '@/shared/errors';
import { usePayments, type CardEntry, type TakenCard } from '@/shared/lib/platform';

import {
  bankRefusal,
  setupRefusal,
  type SetupFailure,
  type SetupRefusal,
} from '../domain/setupRefusal';
import {
  SETUP_START,
  advance,
  canContinue,
  setupSteps,
  waysToPay,
  wordsInForce,
  type SetupEvent,
  type SetupProgress,
  type SetupStep,
} from '../domain/setupSteps';
import {
  isWallet,
  type PayWith,
  type PaymentMethodStanding,
  type SetupOpened,
  type Wallet,
} from '../domain/vocabulary';
import { acceptTerms, openSetup, saveConfirmed } from '../use-cases/paymentMethod';

import { paymentKeys } from './paymentKeys';

/** Which press is in flight — the button it belongs to draws busy. */
export type SetupBusy = 'opening' | 'taking' | 'accepting' | 'asking';

export type { SetupFailure };

export interface PaymentSetupOptions {
  /** The version of the terms' words the screen shows — what *Accept* agrees to. */
  readonly termsVersion: string;
  /** The merchant the wallet's sheet names. */
  readonly walletSheetLabel: string;
  /** The method is saved; the cache already holds it. */
  readonly onSaved: () => void;
}

export interface PaymentSetup {
  readonly steps: readonly SetupStep[];
  readonly chosen: PayWith | null;
  /** Step 1's chips (`waysToPay`). */
  readonly offered: readonly PayWith[];
  readonly canContinue: boolean;
  /** Whether the provider's fields hold a whole card. */
  readonly cardComplete: boolean;
  /** Whether the words the screen shows are the terms in force (`wordsInForce`). */
  readonly wordsInForce: boolean;
  readonly busy: SetupBusy | null;
  readonly failure: SetupFailure | null;
  readonly choose: (payWith: PayWith) => void;
  readonly continueOn: () => void;
  readonly cardChanged: (entry: CardEntry) => void;
  readonly saveCard: () => void;
  readonly acceptTheTerms: () => void;
  readonly askTheBank: () => void;
  /** Press the finished step 1: choose again. */
  readonly reopen: () => void;
}

/**
 * **Everything the setup holds between presses**, in one place because it is dropped in one place:
 * the setup the server opened, its secret, the card the provider took, and whether the bank has
 * already said *saved*. A ref — the presses read it before any render could — and never state: the
 * secret is nothing a render may print.
 */
interface SetupSession {
  readonly opened: SetupOpened | null;
  readonly secret: string | null;
  readonly card: TakenCard | null;
  /** The bank said *saved*; only the server's read of it is left to do. */
  readonly bankSaid: boolean;
}

const NOTHING_HELD: SetupSession = { opened: null, secret: null, card: null, bankSaid: false };

/** The setup's writes fail now rather than wait for a connection. See the module note. */
const NOW_OR_NOT = { networkMode: 'always' } as const;

export function usePaymentSetup({
  termsVersion,
  walletSheetLabel,
  onSaved,
}: PaymentSetupOptions): PaymentSetup {
  const payments = usePayments();
  const client = useQueryClient();

  const [progress, setProgress] = useState<SetupProgress>(SETUP_START);
  /** The progress as of the last move — read by the answers that arrive after a press. */
  const latestProgress = useRef<SetupProgress>(SETUP_START);
  const session = useRef<SetupSession>(NOTHING_HELD);
  /** The terms in force, as the open setup named them — the one part of the session a render reads. */
  const [termsInForce, setTermsInForce] = useState<string | null>(null);
  /** A press is in flight. A ref, so a press arriving before the busy render is still refused. */
  const pending = useRef(false);
  /**
   * Whether the screen is still drawn. The checklist can close under a press in flight — *Keep this
   * one*, the sheet shut — and an answer that lands after that moves nothing and says nothing.
   */
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const [busy, setBusy] = useState<SetupBusy | null>(null);
  const [failure, setFailure] = useState<SetupFailure | null>(null);
  const [cardComplete, setCardComplete] = useState(false);
  const [phoneWallet, setPhoneWallet] = useState<Wallet | null>(null);

  const { mutateAsync: open } = useMutation<SetupOpened, AppError, void>({
    ...NOW_OR_NOT,
    mutationFn: () => openSetup(),
  });
  const { mutateAsync: accept } = useMutation<string | null, AppError, string>({
    ...NOW_OR_NOT,
    mutationFn: (version) => acceptTerms(version),
  });
  const { mutateAsync: save } = useMutation<PaymentMethodStanding, AppError, void>({
    ...NOW_OR_NOT,
    mutationFn: () => saveConfirmed(),
    onSuccess: (standing) => client.setQueryData(paymentKeys.current(), standing),
  });

  useEffect(() => {
    let mounted = true;
    void payments.phoneWallet().then((answer) => {
      if (mounted) setPhoneWallet(answer);
    });
    return () => {
      mounted = false;
    };
  }, [payments]);

  const hold = useCallback((change: Partial<SetupSession>) => {
    session.current = { ...session.current, ...change };
  }, []);

  const move = useCallback((event: SetupEvent): SetupProgress => {
    const before = latestProgress.current;
    const next = advance(before, event);
    latestProgress.current = next;
    setProgress(next);
    // The provider's fields mount empty whenever the card details open — the first time, after a
    // decline, after going back — so what they last said about a whole card is no longer true.
    if (next.open === 'card' && before.open !== 'card') setCardComplete(false);
    return next;
  }, []);

  /**
   * A refusal — the server's or the bank's — turned into what the checklist does next: a start-over
   * drops the whole session, a declined card drops the card, and every refusal is said.
   */
  const refused = useCallback(
    (refusal: SetupRefusal) => {
      switch (refusal.kind) {
        case 'START_OVER':
          session.current = NOTHING_HELD;
          setTermsInForce(null);
          move({ type: 'startedOver' });
          setFailure({ kind: 'SETUP_GONE' });
          return;
        case 'CARD_DECLINED':
          session.current = { ...session.current, card: null, bankSaid: false };
          move({ type: 'declined' });
          setFailure(refusal);
          return;
        default:
          setFailure(refusal);
      }
    },
    [move],
  );

  /** Run one press: refused while another is in flight, busy while it runs. */
  const press = useCallback(async (kind: SetupBusy, work: () => Promise<void>) => {
    if (pending.current) return;
    pending.current = true;
    setBusy(kind);
    setFailure(null);
    try {
      await work();
    } finally {
      pending.current = false;
      setBusy(null);
    }
  }, []);

  const askTheBank = useCallback(
    () =>
      press('asking', async () => {
        const { opened, secret, card, bankSaid } = session.current;
        const chosen = latestProgress.current.chosen;
        if (opened === null || secret === null || chosen === null) return;

        if (!bankSaid) {
          const via = isWallet(chosen)
            ? ({ kind: 'wallet', wallet: chosen, sheetLabel: walletSheetLabel } as const)
            : card === null
              ? null
              : ({ kind: 'card', card } as const);
          if (via === null) return;

          // The provider answers in four words; a rejection is the same as *failed*, never a crash.
          const answer = await payments
            .confirmSetup({
              publishableKey: opened.publishableKey,
              clientSecret: secret,
              with: via,
            })
            .catch(() => 'failed' as const);
          if (!mounted.current) return;
          if (answer !== 'saved') {
            refused(bankRefusal(answer));
            return;
          }
          hold({ bankSaid: true });
        }

        try {
          await save();
          if (mounted.current) onSaved();
        } catch (error) {
          if (mounted.current) refused(setupRefusal(error as AppError));
        }
      }),
    [hold, onSaved, payments, press, refused, save, walletSheetLabel],
  );

  // Arriving at step 4 asks the bank — see the module note. Keyed on the arrival, so a failure
  // that leaves the step open does not ask again on the next render.
  const arrivedAtTheBank = progress.open === 'bank';
  const asked = useRef(false);
  useEffect(() => {
    if (!arrivedAtTheBank) {
      asked.current = false;
      return;
    }
    if (asked.current) return;
    asked.current = true;
    void askTheBank();
  }, [arrivedAtTheBank, askTheBank]);

  const choose = useCallback(
    (payWith: PayWith) => {
      setFailure(null);
      move({ type: 'chose', payWith });
    },
    [move],
  );

  const continueOn = useCallback(async () => {
    if (!canContinue(latestProgress.current.chosen)) return;
    if (session.current.opened !== null) {
      setFailure(null);
      move({ type: 'continued' });
      return;
    }
    await press('opening', async () => {
      try {
        const opened = await open();
        // The fields are drawn after this step opens, so the provider starts first — and a setup
        // is kept only once it has, so *Continue* again tries the start again rather than skip it.
        if (!(await payments.prepare(opened.publishableKey))) {
          setFailure({ kind: 'PROVIDER_NOT_STARTED' });
          return;
        }
        hold({ opened });
        setTermsInForce(opened.termsVersion);
        move({ type: 'continued' });
      } catch (error) {
        setFailure({ kind: 'SAY_SO', error: error as AppError });
      }
    });
  }, [hold, move, open, payments, press]);

  const saveCard = useCallback(
    () =>
      press('taking', async () => {
        const { opened } = session.current;
        if (opened === null) return;
        // The fields are on screen until this answers; a provider that throws is a refusal.
        const taking = await payments
          .takeCard(opened.publishableKey)
          .catch(() => ({ kind: 'refused' as const }));
        if (!mounted.current) return;
        if (taking.kind === 'refused') {
          setFailure({ kind: 'CARD_REFUSED' });
          return;
        }
        hold({ card: taking.card, bankSaid: false });
        move({ type: 'cardSaved' });
      }),
    [hold, move, payments, press],
  );

  const acceptTheTerms = useCallback(
    () =>
      press('accepting', async () => {
        try {
          const secret = await accept(termsVersion);
          if (secret === null) {
            // Accepted again for a card already saved: there is no setup here to confirm, which
            // only a setup cancelled under this screen could mean. Start over rather than guess.
            refused({ kind: 'START_OVER' });
            return;
          }
          hold({ secret });
          move({ type: 'termsAccepted' });
        } catch (error) {
          refused(setupRefusal(error as AppError));
        }
      }),
    [accept, hold, move, press, refused, termsVersion],
  );

  const reopen = useCallback(() => {
    if (pending.current) return;
    setFailure(null);
    hold({ card: null, bankSaid: false });
    move({ type: 'reopened' });
  }, [hold, move]);

  return {
    steps: setupSteps(progress),
    chosen: progress.chosen,
    offered: waysToPay(phoneWallet),
    canContinue: canContinue(progress.chosen),
    cardComplete,
    wordsInForce: wordsInForce(termsVersion, termsInForce),
    busy,
    failure,
    choose,
    continueOn: () => void continueOn(),
    cardChanged: (entry) => setCardComplete(entry.complete),
    saveCard: () => void saveCard(),
    acceptTheTerms: () => void acceptTheTerms(),
    askTheBank: () => void askTheBank(),
    reopen,
  };
}
