/**
 * **The group page's four tabs still fit with a chevron on one of them** (#861, PRD #859; 6.3 as
 * amended) — checked against the real Archivo in the bundle, on the narrowest phone, because no
 * device has drawn the bar at 320pt (the tab menu log's §15 asks for that look).
 *
 * The selected tab that offers its menu widens by the chevron's room (`size.segMenu`) and the four
 * share the rest, so **every label keeps an equal share** — the selected one's beside its chevron.
 * What makes this go red: a longer tab word, a bigger chevron, a fifth tab, or the segment's type
 * growing. Each is a real change to the answer, and none announces itself at 10,5pt.
 *
 * Measured, not asserted: on a 384pt A32 a share is 79,5 and on a 320pt phone 63,5, against
 * *You’re in*'s 44,3 — the widest of the four words.
 */

import { theme } from '@/shared/ui';
import { NARROWEST_SCREEN, readFace, widthOf } from '@/test-support/fontMetrics';

import { GROUP_TABS } from '../domain/groupPage';

import { GROUPS_COPY } from './groupsCopy';

const archivo = readFace(`@expo-google-fonts/archivo/${theme.type.seg.fontFamily}.ttf`);

const { gap, chevron, inset } = theme.size.segMenu;
const ROOM = gap + chevron + inset;

/**
 * One tab's share of the bar at a screen width — the gutters, the track's padding and the gaps
 * between the four taken out, and the chevron's room when one tab draws it.
 */
function shareAt(screen: number, chevronDrawn: boolean): number {
  const track = screen - 2 * theme.size.gutter - 2 * theme.space.xxs;
  const gaps = (GROUP_TABS.length - 1) * theme.space.xxs;
  return (track - gaps - (chevronDrawn ? ROOM : 0)) / GROUP_TABS.length;
}

const words = GROUP_TABS.map((key) => GROUPS_COPY.group.tabs[key]);

describe('the four tabs on the narrowest phone', () => {
  it('fit every word in its share with a chevron drawn on one tab', () => {
    const share = shareAt(NARROWEST_SCREEN, true);

    for (const word of words) {
      expect(widthOf(archivo, word, theme.type.seg.fontSize)).toBeLessThan(share);
    }
  });
});
