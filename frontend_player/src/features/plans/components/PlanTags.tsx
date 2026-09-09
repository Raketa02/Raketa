/**
 * **The plan, read-only — three `Tag`s in `where · day · hour` order.**
 *
 * The second of the two drawings of one plan, and **two components rather than an `editable` prop
 * on one** ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md)
 * §3.1): `PlanCard` takes three mutations, three editors and a sheet, and this takes none. That is
 * `CourtMini` and `CourtBuild`'s own reasoning, where the difference between the two was smaller
 * than it is here.
 *
 * **`Tag`s and not `Chip`s**, which is #338 §7's vocabulary doing exactly what it was split to do
 * — *a pressable pill is a chip*, *tags are never pressable* — and ADR-0149 §4's rule underneath
 * it: **a control that cannot be operated must not offer the affordance of one.** The way to
 * change a slot is the chat door beneath these, and the room is where the chips are.
 *
 * **No dot.** A `Tag`'s dot is the sport's and only the sport's, and these three say nothing about
 * a sport — the screen's eyebrow above them already names it.
 *
 * ## One accessibility element, and it is the reason `Tag` was chosen
 *
 * §24.5: *the three read-only plan tags are one element*, because they are **one fact in three
 * parts with no action** — §20.1 unchanged. The chips in the room are three elements because each
 * one is a way to change something; nothing here is. The sentence is the copy deck's
 * (`planTagsName`), so the place is spoken whole while the tag draws it short.
 */

import { StyleSheet, View } from 'react-native';

import { Tag, theme } from '@/shared/ui';

import { PLAN_SLOTS, type Plan } from '../domain/slots';

import { planTagsName, slotChipLabel } from './planPresentation';

export interface PlanTagsProps {
  /** What has been agreed, and `undefined` where nothing has. The two are one state. */
  readonly plan: Plan | undefined;
}

export function PlanTags({ plan }: PlanTagsProps) {
  return (
    <View style={s.row} accessible accessibilityLabel={planTagsName(plan)}>
      {PLAN_SLOTS.map((slot) => (
        <Tag key={slot} label={slotChipLabel(plan, slot)} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  // Wrapping rather than scrolling, exactly as the card's chip row does: three fit a phone, and
  // the one that can grow is the place — drawn without its court, and taking a second line rather
  // than a gesture on the rare occasion that is still too long.
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});
