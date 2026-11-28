/**
 * **The group sheet and the withdraw sheet** ([#800](https://github.com/Rakieta02/Rakieta/issues/800);
 * the Home rows screens §3.3, §3.5; home rows 6).
 *
 * **One sheet, two faces.** *Asked* on the group sheet opens *Withdraw request*, and two native
 * windows — one leaving while the next arrives — are where iOS drops the second; so the row draws
 * one `BottomSheet` and swaps what is in it. Its title and its one button are the row's to hand in;
 * these are the bodies.
 *
 * ```
 * Ogrody 33 Club                      [Asked] (×)   ← the title row; the one button (`SheetAct`)
 * ┌────┐ Closed group · run by Ogrody 33 · Ogrody 33
 * │ O3 │ ● ● ● ● Padel · Tennis · Squash · Badminton  ← every name written out
 * └────┘
 * ┌──────────────────┐ ┌──────────────────────────┐
 * │ 14               │ │ 11 +3                    │  ← two outlined stat cards, mono
 * │ games this week  │ │ players · new this month │
 * └──────────────────┘ └──────────────────────────┘
 * ▣▣▣▣▣▣ 7 of your friends play here                 ← six faces, not buttons
 * ```
 *
 * **Nothing on the sheet but its button opens anything** (Q26): the faces are a picture of the group,
 * not a way to its members. **No navigation hook here** — a sheet's content keeps the root's contexts
 * only (`CLAUDE.md`); *Open group* is a callback the row answers.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, theme } from '@/shared/ui';

import type { HottestGroup } from '../domain/group';
import { sheetFaces, type SheetButton } from '../domain/hottest';

import { FaceStack } from './FaceStack';
import { GROUPS_COPY } from './groupsCopy';
import { GroupMonogram } from './GroupMonogram';
import {
  gamesThisWeekWords,
  grownBy,
  hottestChipLabel,
  hottestSports,
  identityLine,
  peopleLine,
} from './groupsPresentation';
import { SportDots } from './SportDots';

const HOT = GROUPS_COPY.hottest;

/**
 * **The sheet's one button**, at the title row's right end (the screens §3.5's table) — pills, but
 * *Asked*, which keeps 6.1's corner as home rows 6 draws it.
 */
export function SheetAct({
  button,
  groupName,
  onPress,
}: {
  readonly button: SheetButton;
  readonly groupName: string;
  readonly onPress: (button: SheetButton) => void;
}) {
  const press = () => onPress(button);
  switch (button) {
    case 'join':
    case 'ask':
      return (
        <Button
          label={HOT.chip[button]}
          accessibilityLabel={hottestChipLabel(button, groupName)}
          variant="dark"
          size="sm"
          shape="pill"
          onPress={press}
        />
      );
    case 'requested':
      return (
        <Button
          label={HOT.chip.requested}
          accessibilityLabel={hottestChipLabel('requested', groupName)}
          accessibilityHint={HOT.opensWithdraw}
          variant="waiting"
          size="sm"
          onPress={press}
        />
      );
    case 'open':
      return (
        <Button
          label={HOT.openGroup}
          accessibilityHint={HOT.opensGroup}
          variant="secondary"
          size="sm"
          shape="pill"
          onPress={press}
        />
      );
  }
}

/** The group sheet's body — everything rides on the row's read, so it needs no second one. */
export function GroupSheetBody({ group }: { readonly group: HottestGroup }) {
  const grown = grownBy(group.newThisMonth);
  return (
    <View style={s.body} testID={`group-sheet-${group.id}`}>
      <View style={s.identity}>
        <GroupMonogram monogram={group.monogram} size="sheet" />
        <View style={s.identityWords}>
          <Text style={s.line}>{identityLine(group)}</Text>
          {group.sports.length === 0 ? null : (
            <View style={s.sports}>
              <SportDots sports={group.sports} />
              <Text style={s.line}>{hottestSports(group.sports)}</Text>
            </View>
          )}
        </View>
      </View>

      <View style={s.stats}>
        <Card style={s.stat}>
          <Text style={s.value}>{group.gamesThisWeek}</Text>
          <Text style={s.line}>{gamesThisWeekWords(group.gamesThisWeek)}</Text>
        </Card>
        <Card style={s.stat}>
          <View style={s.valueRow}>
            <Text style={s.value}>{group.memberCount}</Text>
            {grown === undefined ? null : <Growth>{grown}</Growth>}
          </View>
          <Text style={s.line}>{HOT.statPlayers}</Text>
        </Card>
      </View>

      <View style={s.people}>
        <FaceStack
          faces={sheetFaces(group)}
          more={0}
          testIDPrefix={`group-sheet-face-${group.id}-`}
        />
        <Text style={s.line}>{peopleLine(group)}</Text>
      </View>
    </View>
  );
}

/**
 * **The green growth**, *+3* — a gain banked, mono, `mintInk` (1.3 as amended): the sheet's alone
 * since the card dropped *+N this month* (#821).
 */
function Growth({ children }: { readonly children: string }) {
  return <Text style={s.grown}>{children}</Text>;
}

/** **The withdraw sheet's body** — its title says whose answer; this is the one act under it. */
export function WithdrawBody({ onWithdraw }: { readonly onWithdraw: () => void }) {
  return (
    <View style={s.withdraw}>
      <Button label={HOT.withdraw} variant="secondary" size="lg" onPress={onWithdraw} />
    </View>
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.md, paddingTop: theme.space.xs },
  identity: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  identityWords: { flex: 1, gap: theme.space.xs },
  sports: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs, flexWrap: 'wrap' },
  line: { ...theme.type.tiny, color: theme.color.muted, flexShrink: 1 },
  stats: { flexDirection: 'row', gap: theme.space.sm },
  // Outlined, as home rows 6 draws them: 5.1's light card at the sheet's white.
  stat: { flex: 1, gap: theme.space.xxs },
  valueRow: { flexDirection: 'row', alignItems: 'baseline', gap: theme.space.xs },
  value: { ...theme.num.l, ...theme.tabular, color: theme.color.ink },
  grown: {
    ...theme.num.tiny,
    ...theme.tabular,
    fontFamily: theme.font.mono[600],
    color: theme.color.mintInk,
  },
  people: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  withdraw: { paddingTop: theme.space.sm },
});
