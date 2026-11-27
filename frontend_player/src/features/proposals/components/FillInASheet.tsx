/**
 * **The fill, carried into a sheet** ([#817](https://github.com/Raketa02/Raketa/issues/817);
 * ADR-0205 §1) — what a sheet holding *TO CONFIRM* or *FRIENDS GAME* needs of the fill, which it
 * cannot reach by itself.
 *
 * **A sheet keeps the root's contexts only** (`ModalStage`; `docs/architecture.md` Part 13): on
 * Android its content is drawn by the root's overlay host, outside the tabs the fill is mounted
 * around, so `useFill` inside it would find nothing. So the sheet's owner reads the fill where it
 * stands (`useSheetFill`), outside the sheet, and hands it in (`FillInASheet`), which provides it
 * again to what the sheet holds.
 *
 * **And the fill's overlays are drawn inside it while it is up**: the payment confirmation, the
 * setup and *It's a game!* that its tiles open are sheets opened from a sheet, and iOS drops a second
 * native window opened over the first — every sheet opened from a sheet is drawn inside it
 * (design-system 9.1). They go back to the fill's own place when the sheet goes.
 *
 * `over` is what the fill has up — the one part of it the sheet's owner reads itself, to step aside
 * under it.
 */

import { useContext, useId, useLayoutEffect, useMemo, type ReactNode } from 'react';

import {
  FillContext,
  FillHostContext,
  useFill,
  type Fill,
  type FillHost,
  type FillOver,
} from '../hooks/useFill';

/** The fill, as a sheet's owner carries it in. */
export interface SheetFill {
  /** What the fill has up — nothing, a sheet, or *It's a game!*. */
  readonly over: FillOver;
  /** Carried, never read: what `FillInASheet` provides again inside the sheet. */
  readonly fill: Fill;
  readonly host: FillHost;
}

/** The fill, read outside a sheet — under the shell's `FillProvider`. */
export function useSheetFill(): SheetFill {
  const fill = useFill();
  const host = useContext(FillHostContext);
  if (host === undefined) throw new Error('useSheetFill is called under the shell’s FillProvider');
  return useMemo(() => ({ over: fill.over, fill, host }), [fill, host]);
}

export interface FillInASheetProps {
  /** The fill its owner read outside the sheet. */
  readonly fill: SheetFill;
  /** The sheet's content. */
  readonly children: ReactNode;
}

/** Inside a sheet: the fill provided again, and its overlays drawn here while the sheet is up. */
export function FillInASheet({ fill, children }: FillInASheetProps) {
  const here = useId();
  const { enter, hosts, overlays } = fill.host;
  // Before the frame is painted, so an overlay already up is never drawn in both places.
  useLayoutEffect(() => enter(here), [enter, here]);

  return (
    <FillContext.Provider value={fill.fill}>
      <FillHostContext.Provider value={fill.host}>
        {children}
        {hosts[hosts.length - 1] === here ? overlays : null}
      </FillHostContext.Provider>
    </FillContext.Provider>
  );
}
