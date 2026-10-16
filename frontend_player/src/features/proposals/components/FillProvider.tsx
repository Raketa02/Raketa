/**
 * **The moment a yes fills a game, on the phone** — the ten seconds of *Undo* in front of a yes
 * that moves money, the payment setup a first yes needs, *It's a game!*, and the confirmation a
 * refused share needs ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A2.4;
 * the mechanics §6.1, §6.5, §11, §12.2).
 *
 * ## One host, mounted by the shell for the session
 *
 * A yes is said on the deck or on a game's details, and **what it sets going outlives both**: the
 * player swipes *Book it now* and walks back to the group list, or to Home, inside the ten
 * seconds — and the yes is still theirs, the toast still counts with *Undo* under their thumb, and
 * *It's a game!* still lands wherever they are by then. So the countdown, the send and every
 * overlay that answers it live here, above the tabs, and the screens reach them through `useFill`
 * (bound to a screen by `useFillYes`). Everything here is the screens' ephemeral state — a card
 * counting down, a sheet open — held in this component, never a store: a card is the deck read's,
 * and it is only ever *held*, as the deck holds the card in flight. **Where a game opens is the
 * shell's** (`openGame`): this feature never imports the shell that mounts it.
 *
 * ## The ten seconds (§6.5)
 *
 * `book` starts them for a yes `waitsForUndo` — *Book it now*, or any rescue. The toast draws the
 * count and a draining ring; *Undo* drops the yes, and the deck, which hides the card while it
 * counts (`counting`), deals it again where it was. At zero the card leaves the deck's read and the
 * yes is sent, **now or not at all** (`useBookingYes`). **One booking counts at a time**: a second
 * yes that would move money waits for the first to go (the screens hold it, `useFillYes().held`),
 * so no two windows overlap; every other answer goes on. **A yes said again** — after the setup a
 * refusal opened — goes through its ten seconds again if it is one that waits (`yesAgain`): money
 * moves only when ten seconds of *Undo* are up.
 *
 * ## Before a first yes (§6.1, §12.5)
 *
 * With nothing saved (payments' `usePaymentSetupNeeded`, read by the screen that says yes — never
 * here, where it would be read on every launch), a yes opens the payment setup as a sheet
 * (`setUpThen`), and the screen's yes lands when the method is saved — through the ten seconds, if
 * it is one that waits — or is dropped when the sheet closes. The server says the same thing when
 * the read was not in yet (`payment_method_required`), and the same sheet answers it.
 *
 * ## Every yes's answer comes here (`answered`, `refused` → `act`)
 *
 * - **Booked** — every deck, the live yeses, the payments to confirm, Home's games and the receipts
 *   are read again, the details screen it was said on (if still open) goes back to the deck, and
 *   *It's a game!* covers the phone. *Open game* opens it from Home; *Later* leaves the player where
 *   they are.
 * - **Booked on a confirmed payment** (#625, #626; Q110) — a payment in time, or a payment that is
 *   the yes again: *It's a game!* for the player whose payment completed the game (§12.2: *you see
 *   It's a game!*); the others are told *booked · 40 zł held*. A *TO CONFIRM* row holds no card, so
 *   its faces are read off the booking.
 * - **A share to confirm** — *Your payment didn't go through — confirm it to keep your seat*, and
 *   the confirmation opens on that payment, naming the player's time to pay (Q109). Before the club's
 *   cut-off it is their time to fix the card (Q113): *Your card didn't go through — fix it to keep
 *   your seat. Nothing is paid now.* On a rescue the seat is kept for them to take (#640): *… to
 *   take the seat*. A plain yes refused `payment_to_confirm` opens it too, and so does a row of *TO
 *   CONFIRM* (`confirm`).
 * - **No method** — the setup, and the yes again once saved. **Terms needed** — a toast naming You ›
 *   Payments, where they are accepted.
 * - **Waiting for one payment** — the yes filled the game and somebody else's share was refused
 *   (#625; Q110): nobody paid, and the game is on Home *waiting for one payment*. *It's a game!*, with *Waiting for one payment · until 14:40 · Nobody pays until it's
 *   in* under the word — the time is the answer's, so nothing is read for it. A refusal of the
 *   player's own is no screen: their sheet, naming their time.
 * - **A vote** — nothing: seats are still open.
 *
 * **A rescue joined from a *Seats to fill* row** (#557) holds no sides — the row lists the players,
 * not which side the open seat is on — so *It's a game!* observes the booking's read, the seat now
 * taken, and draws its sides once it lands (`ItsAGameFor`); a read that fails says *It's a game!* in
 * a toast, as a confirmation does.
 *
 * A delayed yes refused for a game that is gone — full, over, no longer the player's — leaves the
 * details it was said on, as the details' own refusal does.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { PaymentSetupSheet } from '@/features/payments/types';
import type { AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';
import { announce, theme, UndoToast } from '@/shared/ui';

import { refusalOutcome, rescueGoneOf, type DeckCard, type RescueGone } from '../domain/deck';
import {
  UNDO_WINDOW_MS,
  aPaymentAwaited,
  confirmationOf,
  fillOutcome,
  fillRefusal,
  isRescue,
  seatAtStake,
  undoSecondsLeft,
  waitsForUndo,
  type FillOutcome,
  type ItsAGamePaymentAwaited,
} from '../domain/fill';
import {
  FillContext,
  type BookAsk,
  type ConfirmAsk,
  type Fill,
  type FillAsk,
} from '../hooks/useFill';
import { paymentWindowAt } from '../domain/home';
import { rereadAfterFill, useBookingYes, useConfirmPaymentYes } from '../hooks/useFillWrites';
import { dropCard } from '../hooks/useGroupDeck';
import { useBooking } from '../hooks/useHome';
import { useLatest } from '../hooks/useLatest';

import { ConfirmPaymentSheet } from './ConfirmPaymentSheet';
import { refusalMessage } from './deckPresentation';
import { RescueGoneSheet } from './RescueGoneSheet';
import { FILL_COPY } from './fillCopy';
import { bookingAnnouncement, bookingIn, refusedToast } from './fillPresentation';
import { ItsAGame } from './ItsAGame';

interface Counting extends BookAsk {
  readonly endsAt: number;
}

/**
 * **What *It's a game!* is raised for** — a game booked, or one waiting for one payment (Q110): the
 * booking, the sides the yes held if it held any, and for the second until when.
 */
interface Celebrating {
  readonly bookingId: string;
  readonly sides?: DeckCard['sides'];
  readonly missing?: ItsAGamePaymentAwaited;
}

export interface FillProviderProps {
  /** How far above the bottom inset the toast sits — the bar's height while the bar is drawn. */
  readonly toastAbove: number;
  /** *Open game* — the shell's move: Home laid down, the booked game's details over it (#556). */
  readonly openGame: (bookingId: string) => void;
  readonly children: ReactNode;
}

export function FillProvider({ toastAbove, openGame, children }: FillProviderProps) {
  const client = useQueryClient();
  const insets = useSafeAreaInsets();

  const [counting, setCounting] = useState<Counting | null>(null);
  /** Re-rendered once a second while a booking counts down — the toast's words. */
  const [, setTick] = useState(0);
  const [settingUp, setSettingUp] = useState<{ readonly then?: () => void } | null>(null);
  const [confirming, setConfirming] = useState<ConfirmAsk | null>(null);
  /** *It's a game!* up — with the sides the yes held, or read off the booking when it held none. */
  const [celebrating, setCelebrating] = useState<Celebrating | null>(null);
  /** A rescue whose booking or seat went while it was reached for — the sheet says why. */
  const [gone, setGone] = useState<RescueGone | undefined>(undefined);

  const book = useCallback<Fill['book']>((ask) => {
    const endsAt = Date.now() + UNDO_WINDOW_MS;
    // One window at a time: the screens hold a second booking, and this is the backstop.
    setCounting((running) => running ?? { ...ask, endsAt });
    announce(bookingAnnouncement(undoSecondsLeft(endsAt, Date.now())), 'queued');
  }, []);

  /**
   * A rescue refused because its booking or its seat went — taken, called off, under way, or no
   * longer offered to them: a sheet the player must close, in place of a toast they can miss — and
   * nothing was charged. `true` when it took the refusal.
   */
  const sayRescueGone = (error: AppError, ask: FillAsk): boolean => {
    const reason = rescueGoneOf(error.code, error.details);
    if (reason === undefined || ask.card === undefined || !isRescue(ask.card)) return false;
    setGone(reason);
    if (refusalOutcome(error.code) === 'gone') ask.leave?.();
    return true;
  };

  /** What a screen, a sheet or the delayed send does next — read off one outcome, in one place. */
  const act = (outcome: FillOutcome, ask: FillAsk, then?: () => void) => {
    const sides = ask.card?.sides;
    const held = sides === undefined ? {} : { sides };
    switch (outcome.kind) {
      case 'booked': {
        void rereadAfterFill(client);
        ask.leave?.();
        // A Seats to fill row, or a TO CONFIRM row, holds no sides: the overlay reads them off the
        // booking.
        setCelebrating({ bookingId: outcome.bookingId, ...held });
        return;
      }
      case 'paymentAwaited':
        // The game is on Home now, waiting for one payment; nothing was charged (#625). The players
        // are matched (Q110): It's a game!, with until when — the answer's own time.
        void rereadAfterFill(client);
        setCelebrating({
          bookingId: outcome.bookingId,
          ...held,
          missing: aPaymentAwaited(outcome.until, Date.now()),
        });
        return;
      case 'confirm':
        showToast({
          message: refusedToast(
            paymentWindowAt(outcome.confirmBy, outcome.timeTo, Date.now()),
            seatAtStake(ask.card),
          ),
          tone: 'bad',
        });
        setConfirming({ ...ask, ...confirmationOf(outcome) });
        return;
      case 'setUp':
        setSettingUp(then === undefined ? {} : { then });
        return;
      case 'termsAgain':
        showToast({ message: FILL_COPY.termsAgain, tone: 'bad' });
        return;
      case 'counted':
        return;
    }
  };

  /** The yes again, the fill's own way: through its ten seconds if it is one that waits. */
  const yesAgain = (ask: FillAsk): (() => void) | undefined => {
    const { card } = ask;
    if (card === undefined) return undefined;
    return () => (waitsForUndo(card) ? book({ ...ask, card }) : sendYes({ ...ask, card }));
  };

  /** The two above as of the last render, for the callbacks that outlive it. */
  const latest = useLatest({ act, yesAgain });

  // `mutate` and `mutateAsync` are stable across renders; the results around them are not.
  const { mutate: sendYes } = useBookingYes({
    onAnswered: (answer, ask) =>
      latest.current.act(fillOutcome(answer), ask, latest.current.yesAgain(ask)),
    onRefused: (error, ask) => {
      if (sayRescueGone(error, ask)) return;
      const mended = fillRefusal(error.code, error.details);
      if (mended !== undefined) {
        latest.current.act(mended, ask, latest.current.yesAgain(ask));
        return;
      }
      showToast({ message: refusalMessage(error), tone: 'bad' });
      if (refusalOutcome(error.code) === 'gone') ask.leave?.();
    },
  });

  const { mutateAsync: confirmPayment } = useConfirmPaymentYes({
    onAnswered: (answer, ask) => {
      const outcome = fillOutcome(answer);
      setConfirming((open) => (open?.seatChargeId === ask.seatChargeId ? null : open));
      if (outcome.kind === 'counted') showToast({ message: FILL_COPY.confirm.kept, tone: 'ok' });
      latest.current.act(outcome, ask, latest.current.yesAgain(ask));
    },
    // The confirmation says its own refusals, in the sheet the player is looking at.
    onRefused: () => undefined,
  });

  const answered = useCallback<Fill['answered']>(
    (answer, ask) => latest.current.act(fillOutcome(answer), ask, latest.current.yesAgain(ask)),
    [latest],
  );

  const refused = useCallback<Fill['refused']>(
    (error, ask, retry) => {
      if (sayRescueGone(error, ask)) return true;
      const mended = fillRefusal(error.code, error.details);
      if (mended === undefined) return false;
      latest.current.act(mended, ask, retry);
      return true;
    },
    [latest],
  );

  // The count: a tick a second for the toast's words, and the send at zero. The card leaves the
  // deck's read as it is sent, so the deck does not deal it again while the answer is on its way.
  useEffect(() => {
    if (counting === null) return undefined;
    let timer: ReturnType<typeof setTimeout>;
    const tick = () => {
      const left = counting.endsAt - Date.now();
      if (left > 0) {
        setTick((n) => n + 1);
        timer = setTimeout(tick, Math.min(1_000, left));
        return;
      }
      const { endsAt: _sent, ...ask } = counting;
      dropCard(client, ask.dealtIn, ask.card.proposalId);
      setCounting(null);
      sendYes(ask);
    };
    timer = setTimeout(tick, Math.min(1_000, counting.endsAt - Date.now()));
    return () => clearTimeout(timer);
  }, [counting, client, sendYes]);

  const fill = useMemo<Fill>(
    () => ({
      counting: counting?.card.proposalId ?? null,
      book,
      setUpThen: (then) => setSettingUp({ then }),
      confirm: setConfirming,
      answered,
      refused,
    }),
    [counting, book, answered, refused],
  );

  return (
    <FillContext.Provider value={fill}>
      {children}

      {counting === null ? null : (
        <View
          pointerEvents="box-none"
          style={[s.toastHost, { bottom: toastAbove + insets.bottom + theme.space.sm }]}
        >
          <UndoToast
            message={bookingIn(undoSecondsLeft(counting.endsAt, Date.now()))}
            actionLabel={FILL_COPY.undo.action}
            actionAccessibilityLabel={FILL_COPY.undo.actionSpoken}
            onAction={() => setCounting(null)}
            endsAt={counting.endsAt}
            windowMs={UNDO_WINDOW_MS}
          />
        </View>
      )}

      <PaymentSetupSheet
        visible={settingUp !== null}
        onClose={() => setSettingUp(null)}
        onSaved={() => {
          const then = settingUp?.then;
          setSettingUp(null);
          then?.();
        }}
      />

      <RescueGoneSheet gone={gone} onClose={() => setGone(undefined)} />

      {confirming === null ? null : (
        <ConfirmPaymentSheet
          key={confirming.seatChargeId}
          seatChargeId={confirming.seatChargeId}
          confirmBy={confirming.confirmBy}
          timeTo={confirming.timeTo}
          seat={seatAtStake(confirming.card)}
          onClose={() => setConfirming(null)}
          yesAgain={() => confirmPayment(confirming)}
        />
      )}

      {celebrating === null ? null : (
        <ItsAGameFor
          {...celebrating}
          onLater={() => setCelebrating(null)}
          onOpenGame={() => {
            setCelebrating(null);
            openGame(celebrating.bookingId);
          }}
          onUnreadable={() => {
            setCelebrating(null);
            showToast({ message: FILL_COPY.itsAGameInHome, tone: 'ok' });
          }}
        />
      )}
    </FillContext.Provider>
  );
}

/** What *It's a game!* does with its doors, and with a booking it cannot draw. */
interface ItsAGameDoors {
  readonly onLater: () => void;
  readonly onOpenGame: () => void;
  readonly onUnreadable: () => void;
}

/**
 * ***It's a game!* for one booking** — booked, or waiting for one payment — drawn from the sides the
 * yes held, or, for a *Seats to fill* row's join, from the booking's own read (`useBooking`),
 * observed for as long as the overlay waits for it: nothing is drawn until it lands, and a booking
 * that cannot be read — refused, or in a sport this build cannot name — says *It's a game!* in a
 * toast instead. A game waiting for one payment carries its line, whose time is the answer's (Q110).
 */
function ItsAGameFor({
  bookingId,
  sides,
  missing,
  onLater,
  onOpenGame,
  onUnreadable,
}: ItsAGameDoors & Celebrating) {
  const read = useBooking(bookingId, { enabled: sides === undefined });
  const drawn = sides ?? read.data?.sides;
  const unreadable = sides === undefined && (read.data === null || read.isError);
  useWhenUnreadable(unreadable, onUnreadable);

  if (drawn === undefined) return null;
  return (
    <ItsAGame card={{ sides: drawn }} missing={missing} onLater={onLater} onOpenGame={onOpenGame} />
  );
}

/** Says the booking could not be drawn, once it is known — the toast in place of the screen. */
function useWhenUnreadable(unreadable: boolean, onUnreadable: () => void) {
  const settle = useLatest(onUnreadable);
  useEffect(() => {
    if (unreadable) settle.current();
  }, [unreadable, settle]);
}

const s = StyleSheet.create({
  // 9.2's place for a toast — the gutter's inset either side, above the bar — on the toast layer.
  toastHost: {
    position: 'absolute',
    left: theme.space.lg,
    right: theme.space.lg,
    zIndex: theme.layer.toast,
  },
});
