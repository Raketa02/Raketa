/**
 * **One plan slot on the Now card** — a bar, a label and a value; bright where the slot is
 * settled and dim where it is not
 * ([#413](https://github.com/Raketa02/Raketa/issues/413),
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §4.2).
 *
 * Three of these, in the app's own order, are the card's whole account of the plan: the card
 * fills with brightness as the plan does. What used to be a figure, a line and a gloss — one
 * large value, the rest on a line, and *Still to agree: the day* in prose — is three rows that
 * each say their slot's name and what it holds, and **an unfilled one says `Not agreed yet`**
 * under a dim bar rather than naming itself.
 *
 * ## The settled bar is 5.4's 3pt bar, on dark
 *
 * The third drawing of `size.semanticBar` — the note wears it as a border, the challenge row as
 * a stripe, and this row as a stripe too, at the row stripe's own shape (`radius.bar`,
 * `alignSelf: stretch`). What differs is the meaning and the ground: **bright is agreed, dim is
 * not**, in the card's accent over `night`, where the row's stripe is amber presence over paper.
 * Part 13's *never colour alone* is discharged by the value beside it, which says the same thing
 * in words — the bar is the sighted reader's copy, and it is not an element of its own.
 *
 * ## Three drawings of a value, chosen by the slot and not by a regular expression
 *
 * The **place** is `h2` in white, one line, tail-ellipsised — #335's *shorter value, not a second
 * line* through `placeWithoutTheCourt`. The whole place is the text's own label as the ticket
 * asks, and it is inert while the card's body is the element: what a listener actually hears is
 * the body's name, which speaks the place whole (`cardSlotSpoken`). The **day**
 * is the weekday whole in `h2` and the date beside it in `tiny`: `Sunday` `9 Aug`. The **hour** is
 * `num.m`, because [1.4](../../../../docs/design-system.md#14-numbers-are-monospaced-always) is
 * categorical that numbers are monospaced always, and it is the mono role whose optical size sits
 * beside `h2`'s. Which drawing it is comes off the slot's name — a component branching on `/^\d/`
 * would be that decision made by a regular expression.
 *
 * **Every value box is `h2`'s line tall, whatever it holds.** `Not agreed yet` is `tiny`, and a
 * row that shrank when its slot was empty would put the bars at three different heights on one
 * card and move the court beside them when a slot filled — the layout jump #410 names as the
 * reason every card is drawn by one shell.
 */

import { StyleSheet, Text, View } from 'react-native';

import { dayDate } from '@/shared/date/calendarDay';
import { placeWithoutTheCourt } from '@/shared/formatting/placeName';
import { theme } from '@/shared/ui';

import { slotValue, type Plan, type PlanSlot } from '../domain/slots';

import { NOT_AGREED_YET, SLOT_EYEBROW, dayChipName } from './planPresentation';

export interface SlotRowProps {
  readonly slot: PlanSlot;
  readonly plan: Plan | undefined;
  /** The bar's colour where the slot is settled — the card's accent, from `ACCENT[name]`. */
  readonly accent: string;
}

export function SlotRow({ slot, plan, accent }: SlotRowProps) {
  const value = slotValue(plan, slot);

  return (
    <View style={s.row}>
      <View
        style={[s.bar, { backgroundColor: value === undefined ? theme.color.onDarkHair : accent }]}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
      <View style={s.text}>
        <Text style={s.label}>{SLOT_EYEBROW[slot]}</Text>
        <View style={s.value}>
          {value === undefined ? (
            <Text style={s.unsettled}>{NOT_AGREED_YET}</Text>
          ) : (
            <SettledValue slot={slot} value={value} />
          )}
        </View>
      </View>
    </View>
  );
}

function SettledValue({ slot, value }: { readonly slot: PlanSlot; readonly value: string }) {
  if (slot === 'where') {
    return (
      <Text style={s.place} numberOfLines={1} ellipsizeMode="tail" accessibilityLabel={value}>
        {placeWithoutTheCourt(value)}
      </Text>
    );
  }

  if (slot === 'day') {
    return (
      <View style={s.day}>
        <Text style={s.weekday} numberOfLines={1}>
          {dayChipName(value)}
        </Text>
        <Text style={s.date} numberOfLines={1}>
          {dayDate(value)}
        </Text>
      </View>
    );
  }

  return <Text style={s.hour}>{value}</Text>;
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', gap: theme.space.sm },
  // The row stripe's shape: full height, and the bar's radius rather than a square end.
  bar: {
    width: theme.size.semanticBar,
    alignSelf: 'stretch',
    borderRadius: theme.radius.bar,
  },
  text: { flex: 1, gap: theme.space.xxs },
  label: { ...theme.type.eyebrow, color: theme.color.onDarkEyebrow, textTransform: 'uppercase' },
  // `h2`'s line, always — see the module note.
  value: { minHeight: theme.type.h2.lineHeight, justifyContent: 'center' },
  unsettled: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  place: { ...theme.type.h2, color: theme.color.surface },
  day: { flexDirection: 'row', alignItems: 'baseline', gap: theme.space.xs },
  weekday: { ...theme.type.h2, color: theme.color.surface, flexShrink: 1 },
  date: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  hour: { ...theme.num.m, ...theme.tabular, color: theme.color.surface },
});
