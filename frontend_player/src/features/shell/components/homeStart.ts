/**
 * **Home, back at its start** — what a press that lands on Home tells the Home that is already up.
 *
 * Home is laid down once and kept underneath every tab (`TAB_STACK`), so landing on it is a pop
 * back to a screen that never went away — and a kept screen keeps its scroll. *Pressing a tab goes
 * to that tab's start* is the shell's rule, and for a screen that was drawn fresh on every press the
 * start was free; for one that is kept, it has to be asked for. This is the asking: the shell's
 * landing moves say so here, and Home's page, the one screen subscribed, puts its scroller back at
 * the top.
 *
 * **Only a landing says it, never a return.** *Back* from a screen pushed over Home — a game, a See
 * all — goes where the player was, scroll and all, and nothing here is told about it.
 *
 * Module state rather than a context because the shell's navigation moves are not render paths
 * (`shellNavigation`'s own reason for the imperative `router`), and the one listener is the one Home.
 */

type Listener = () => void;

const listeners = new Set<Listener>();

/** Subscribe to landings on Home; the answer unsubscribes. */
export function whenHomeStartsOver(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Tell the kept Home that a press landed on it, so it shows its start. */
export function sendHomeToItsStart(): void {
  for (const listener of listeners) listener();
}
