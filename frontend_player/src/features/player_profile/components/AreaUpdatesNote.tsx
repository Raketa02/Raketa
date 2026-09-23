/**
 * The one sentence about the Location area — **static, and the only written trace that it
 * moves** ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6).
 *
 * Nothing else is drawn about it: no cell, no *last updated*. An area is a coordinate string
 * nobody can read and the refresh is deliberately silent, so what a player is owed is the rule
 * and not a log — one line of `tiny` in `muted`. It sat at the foot of the You tab for as long
 * as the tab was a placeholder; it is now inside *Where you play*, under *Your area is set*,
 * because that is the screen about the area and the row's live line is the short form of it
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 */

import { StyleSheet, Text } from 'react-native';

import { theme } from '@/shared/ui';

import { AREA_UPDATES_LINE } from './locationPresentation';

export function AreaUpdatesNote() {
  return <Text style={s.line}>{AREA_UPDATES_LINE}</Text>;
}

const s = StyleSheet.create({
  line: { ...theme.type.tiny, color: theme.color.muted },
});
