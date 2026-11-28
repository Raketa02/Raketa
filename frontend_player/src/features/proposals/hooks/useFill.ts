/**
 * **What a screen that says yes may ask of the fill** — the contract `FillProvider` serves and
 * `useFillYes` binds to a screen ([#555](https://github.com/Rakieta02/Rakieta/issues/555)). Here, in
 * `hooks/`, so a hook can reach it without importing a component.
 */

import { createContext, useContext, type ReactNode } from 'react';

import type { AppError } from '@/shared/errors';

import type { DeckCard } from '../domain/deck';
import type { Confirmation, DealtIn, YesAnswer, YesOn } from '../domain/fill';
import type { TimeTo } from '../domain/vocabulary';

/**
 * A yes the fill acts on: the deck it was dealt in, what it was said on — absent for a
 * confirmation opened from You › Payments, where no game is held — and the screen to leave once it
 * books (the details, still on screen).
 */
export interface FillAsk {
  readonly card?: YesOn;
  readonly dealtIn: DealtIn;
  readonly leave?: () => void;
}

/** A yes the fill sends itself — always on a game held: a card, a game's details, a rescue's row. */
export interface BookAsk extends FillAsk {
  readonly card: YesOn;
}

/**
 * A refused share to confirm, and the yes it carries — with their time to pay when whoever opens it
 * knows it (#625, #626): the sheet names it.
 */
export interface ConfirmAsk extends FillAsk, Confirmation {}

/**
 * **A share to confirm that no yes carries** — a friends game's *Accept* the bank wants checked, or a
 * card it declined (#759) — confirmed its own way (#817): `yesAgain` is the answer again once the
 * payment is confirmed, and a refusal of it is said in the sheet in `refusal`'s words. The sheet
 * closes once `yesAgain` resolves.
 */
export interface OwnConfirmation {
  readonly seatChargeId: string;
  readonly confirmBy?: string;
  readonly timeTo?: TimeTo;
  readonly refusal: (error: AppError) => string | undefined;
  readonly yesAgain: () => Promise<unknown>;
}

/**
 * **What the fill has up over the phone** (#817) — nothing; a sheet: the payment setup, a refused
 * share's confirmation, a rescue gone; or ***It's a game!***, which outranks a sheet. Needs your
 * answer reads it to step aside under what it opened, and to close for good after *It's a game!*.
 */
export type FillOver = 'none' | 'sheet' | 'itsAGame';

export interface Fill {
  /** The proposal whose yes is counting down behind *Undo* — hidden from the deck — or `null`. */
  readonly counting: string | null;
  /** What the fill has up: nothing, a sheet, or *It's a game!*. */
  readonly over: FillOver;
  /** Start the ten seconds in front of a yes that moves money. Refused while one counts. */
  readonly book: (ask: BookAsk) => void;
  /** Open the payment setup, and run `then` once the method is saved. */
  readonly setUpThen: (then: () => void) => void;
  /** Open the confirmation on a refused share. */
  readonly confirm: (ask: ConfirmAsk) => void;
  /**
   * Open the confirmation on a share no yes carries — confirmed its own way. The fill draws it, so a
   * sheet that carries the fill in has it drawn over it, as every other sheet the fill opens.
   */
  readonly confirmOwn: (ask: OwnConfirmation) => void;
  /** A yes's answer, sent from anywhere. */
  readonly answered: (answer: YesAnswer, ask: FillAsk) => void;
  /**
   * The refusals the fill mends itself (`fillRefusal`): no saved method — the setup, then `retry` —
   * and a payment to confirm. `true` when it took the refusal, so the screen says nothing.
   */
  readonly refused: (error: AppError, ask: FillAsk, retry?: () => void) => boolean;
  /**
   * ***It's a game!*** for a booking made whole by something other than a yes — a friend's *Accept*
   * that took a friends game's last seat (#759) — with the sides the card held, or read off the
   * booking when it held none. Every read a booking changes is read again.
   */
  readonly celebrate: (bookingId: string, sides?: DeckCard['sides']) => void;
}

export const FillContext = createContext<Fill | undefined>(undefined);

/**
 * **Where the fill's overlays are drawn** (#817) — its sheets and *It's a game!*: at the provider, or
 * inside the newest sheet that hosts them (`FillInASheet`), so a sheet the fill opens from a sheet is
 * drawn inside it, as every sheet opened from a sheet is (design-system 9.1).
 */
export interface FillHost {
  /** The overlays, as the provider last drew them. */
  readonly overlays: ReactNode;
  /** The sheets hosting them, oldest first: the newest draws them. */
  readonly hosts: readonly string[];
  /** A sheet starts hosting them; the answer stops it. */
  readonly enter: (host: string) => () => void;
}

export const FillHostContext = createContext<FillHost | undefined>(undefined);

/** The fill, for a screen under the shell. */
export function useFill(): Fill {
  const fill = useContext(FillContext);
  if (fill === undefined) throw new Error('useFill is called under the shell’s FillProvider');
  return fill;
}
