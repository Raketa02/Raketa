/**
 * **What a screen that says yes may ask of the fill** — the contract `FillProvider` serves and
 * `useFillYes` binds to a screen ([#555](https://github.com/Raketa02/Raketa/issues/555)). Here, in
 * `hooks/`, so a hook can reach it without importing a component.
 */

import { createContext, useContext } from 'react';

import type { AppError } from '@/shared/errors';

import type { DealtIn, YesAnswer, YesOn } from '../domain/fill';

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

/** A refused share to confirm, and the yes it carries. */
export interface ConfirmAsk extends FillAsk {
  readonly seatChargeId: string;
}

export interface Fill {
  /** The proposal whose yes is counting down behind *Undo* — hidden from the deck — or `null`. */
  readonly counting: string | null;
  /** Start the ten seconds in front of a yes that moves money. Refused while one counts. */
  readonly book: (ask: BookAsk) => void;
  /** Open the payment setup, and run `then` once the method is saved. */
  readonly setUpThen: (then: () => void) => void;
  /** Open the confirmation on a refused share. */
  readonly confirm: (ask: ConfirmAsk) => void;
  /** A yes's answer, sent from anywhere. */
  readonly answered: (answer: YesAnswer, ask: FillAsk) => void;
  /**
   * The refusals the fill mends itself (`fillRefusal`): no saved method — the setup, then `retry` —
   * and a payment to confirm. `true` when it took the refusal, so the screen says nothing.
   */
  readonly refused: (error: AppError, ask: FillAsk, retry?: () => void) => boolean;
}

export const FillContext = createContext<Fill | undefined>(undefined);

/** The fill, for a screen under the shell. */
export function useFill(): Fill {
  const fill = useContext(FillContext);
  if (fill === undefined) throw new Error('useFill is called under the shell’s FillProvider');
  return fill;
}
