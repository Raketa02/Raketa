/**
 * You's one sentence about the Location area — **static, and the only written trace that it
 * moves** ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6).
 *
 * Nothing else is drawn about it: no cell, no *last updated*, no control. An area is a
 * coordinate string nobody can read and the refresh is deliberately silent, so what a player
 * is owed is the rule and not a log — one line of `tiny` in `muted`, the register the tab's
 * other footnotes already take, under the profile block and above the account panel.
 *
 * It is this feature's and not the shell's, for `PlayIntentsSection`'s reason: the sentence is
 * about a fact the profile holds and a write the profile owns, and the shell composes it as it
 * composes the section above it.
 */

import { StyleSheet, Text } from 'react-native';

import { theme } from '@/shared/ui';

import { AREA_UPDATES_LINE } from './locationPresentation';

export function AreaUpdatesNote() {
  return <Text style={s.line}>{AREA_UPDATES_LINE}</Text>;
}

const s = StyleSheet.create({
  line: { ...theme.type.tiny, color: theme.color.muted, paddingTop: theme.space.md },
});
