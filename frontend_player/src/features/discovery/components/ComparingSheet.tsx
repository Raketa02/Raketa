/**
 * **Which card's comparison is up** — Home's row and See all keep the same state: whose sheet it is,
 * and whether it is open (#802).
 *
 * - **The sheet draws the latest read of the person**, so a friend write that re-reads the list
 *   moves its button too (the Home rows screens §8.5).
 * - **A write can move them out of the list** — asking a fresh match makes them a gap, and on a row
 *   with more fresh matches than places the next one takes theirs (the mechanics §9.1). **The sheet
 *   then closes, drawn as they last were** rather than emptying under the thumb, and the card leaves
 *   with them (a call: the sheet has nowhere left to read them from).
 * - **It never reopens by itself**: a later read bringing them back leaves it shut until it is
 *   tapped, as the round button's own sheets do.
 */

import { useState } from 'react';

import type { SameLevelPlayer } from '../domain/sameLevel';

import { ComparisonSheet } from './ComparisonSheet';

export interface Comparing {
  /** Whom the sheet compares — their latest read, kept as it was once they leave the list. */
  readonly player: SameLevelPlayer | undefined;
  readonly open: boolean;
  readonly show: (player: SameLevelPlayer) => void;
  readonly close: () => void;
}

export function useComparing(players: readonly SameLevelPlayer[]): Comparing {
  const [shown, setShown] = useState<SameLevelPlayer>();
  const [open, setOpen] = useState(false);
  const current =
    shown === undefined ? undefined : players.find((player) => player.playerId === shown.playerId);
  if (current !== undefined && current !== shown) setShown(current);
  if (open && shown !== undefined && current === undefined) setOpen(false);

  return {
    player: current ?? shown,
    open,
    show: (player) => {
      setShown(player);
      setOpen(true);
    },
    close: () => setOpen(false),
  };
}

export function ComparingSheet({ comparing }: { readonly comparing: Comparing }) {
  if (comparing.player === undefined) return null;
  return (
    <ComparisonSheet visible={comparing.open} player={comparing.player} onClose={comparing.close} />
  );
}
