/**
 * **Match me** — the second Play surface, and the second screen inside the tab.
 *
 * A sibling of `play/index.tsx` rather than a screen behind it: Find a game stays underneath,
 * so the platform's own back gesture comes back out of the deck, and the bar's active column
 * is read off the first path segment and stays on ⚡Play throughout.
 */

import { DeckScreen } from '@/features/play/types';

export default function DeckRoute() {
  return <DeckScreen />;
}
