/**
 * **Players** — the deck, and the whole of the tab
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1).
 *
 * A single-screen root like the three flanking tabs, and named by `features/play` rather than
 * by the shell: the deck is that feature's surface and it was under Play until it earned a
 * column of its own. The shell keeps no per-tab history, so Players opens on the deck every
 * time — the held deal is what makes that cheap.
 */

import { DeckScreen } from '@/features/play/types';

export default function PlayersRoute() {
  return <DeckScreen />;
}
