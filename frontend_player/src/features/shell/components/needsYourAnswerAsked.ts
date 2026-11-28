/**
 * **Home, with Needs your answer up** ([#817](https://github.com/Rakieta02/Rakieta/issues/817),
 * ADR-0205 §1; Q25) — where a link or a notice that pointed at one of the sheet's cards lands now:
 * the friend link, a friends game invitation's notice and a friend request's.
 *
 * **Home is laid down as the tab bar lays it** (`openTab`), and the kept Home's sheet is told it was
 * asked for. It opens **once the reads the link or the notice re-read have landed, and only if
 * something waits by then** (`needsYourAnswer`'s `asked`): a crossing request made friends, or one a
 * block swallowed, lands on Home as it is, and the sheet is never shown empty.
 *
 * **The ask is held until a sheet takes it.** Home is kept under every tab, so it is almost always
 * there to hear it — but a stack that began somewhere else, a link opened straight onto `/you`, gets
 * its Home from `openTab` itself, mounted after this has spoken. So the ask is kept, and the Home
 * that subscribes next takes it; a sheet that hears it at once takes it there and then, and nothing
 * is left over.
 *
 * Module state rather than a context, for `homeStart`'s reason: the callers are a link's answer and
 * a notice's tap, not render paths, and the one listener is the one Home.
 */

import { openTab } from './shellNavigation';

type Listener = () => void;

const listeners = new Set<Listener>();

/** An ask no sheet has taken yet. */
let held = false;

/** Subscribe to the sheet being asked for — an ask still held is heard at once; the answer unsubscribes. */
export function whenNeedsYourAnswerAsked(listener: Listener): () => void {
  listeners.add(listener);
  if (held) {
    held = false;
    listener();
  }
  return () => {
    listeners.delete(listener);
  };
}

/**
 * Open Home with Needs your answer up — from `where`, the pathname the player is on, as `openTab`
 * takes it. On Home already, nothing is laid down and the sheet is still asked for.
 */
export function openNeedsYourAnswer(where: string): void {
  openTab('home', where);
  if (listeners.size === 0) {
    held = true;
    return;
  }
  for (const listener of listeners) listener();
}
