/**
 * The *Deck | Radar* toggle — the Players tab's whole header, in its lead slot
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1), drawn on paper over the deck and on the night over the radar.
 *
 * One component rather than a `Segment` written twice, because the two panes are two frames —
 * the deck's `ShellScreen` and the radar's own dark one — and each needs the same two options
 * in the same order with the same names, differing only in whether the control is on dark
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7). The options and their words are `deckPresentation`'s; this is where they are put on
 * the control.
 */

import { StyleSheet } from 'react-native';

import { Segment } from '@/shared/ui';

import { PANE_LABEL, type PlayersPane } from './deckPresentation';

export interface PlayersToggleProps {
  readonly pane: PlayersPane;
  readonly onSelect: (pane: PlayersPane) => void;
  readonly onDark?: boolean;
}

export function PlayersToggle({ pane, onSelect, onDark = false }: PlayersToggleProps) {
  return (
    <Segment
      selected={pane}
      options={[
        { key: 'deck', label: PANE_LABEL.deck },
        { key: 'radar', label: PANE_LABEL.radar },
      ]}
      onSelect={onSelect}
      onDark={onDark}
      // `flex: 1` on the track is what gives its two segments a width to share.
      style={s.toggle}
    />
  );
}

const s = StyleSheet.create({
  toggle: { flex: 1 },
});
