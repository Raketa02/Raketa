/**
 * **The plan card** — pinned under the room's header, and the three slot chips and nothing else
 * ([#366](https://github.com/Raketa02/Raketa/issues/366),
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3.2).
 *
 * **Pinned**, because every chat opens at its newest entry — that is what a cursor is for — so a
 * card in the scroll is a card you have to hunt for, and the plan is the thing the room exists to
 * fill. **The chips alone**, because the panel that explains them is permanent chrome above a
 * composer and already has a home: the game screen, where the plan is read
 * ([ADR-0145](../../../../../docs/adr/0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md)
 * §6). One panel, one home.
 *
 * ## `Chip`s here and `Tag`s there, and that is not a variant
 *
 * *A pressable pill is a chip*, *tags are never pressable* — the vocabulary doing exactly what it
 * was split to do (#338 §7). The read-only rendering is a **second component in this feature**
 * rather than an `editable` prop on this one, on `CourtMini` and `CourtBuild`'s own reasoning:
 * here the difference is larger, because one takes three mutations and three input surfaces and
 * the other takes none.
 *
 * ## There is no lock, and there is nothing to draw about one
 *
 * ADR-0144 deleted *Lock it in*, the locked border and the `locked by everybody` pill: **filling
 * the third slot is the lock**, the button existed to unlock ownership and booking and both are
 * out of scope, and the pill is a phrase the data cannot support since no assent is recorded
 * anywhere and a slot is set by whoever tapped last. So this card has no complete state, no
 * border that changes and no count.
 *
 * **Any member may fill or change any slot, any number of times.** There is no rate limit — *the
 * line is the friction* — and **a slot is never emptied**: every chip opens an editor whether or
 * not it already holds a value, and none of the three editors offers a way to clear one.
 *
 * ## No optimistic write, and the card is where that is visible
 *
 * *Pending, never optimistic* is this map's rule for everything that reaches another person, and a
 * slot change writes a system line other people read. So the chip goes **busy with the value it
 * already had** — never the value being written — and **the line arrives through the stream like
 * any other entry**, on the nudge every other member's copy of it arrives on.
 *
 * That is also why this card, rather than a sheet, is what reports. Each editor **closes on the
 * press**, so the card is the surface a player is looking at when the answer lands, and it draws
 * three things under the row: the refusal, the pause, and nothing at all when neither.
 *
 * - **A refusal is written copy rather than a disabled control**, which is §22.2's own reason: the
 *   day and the hour are filled in either order, so either one can be the second and the sentence
 *   names both remedies — with both chips directly above it.
 * - **A paused write is not a failed one**, so it says so where the pause is: `networkMode` is the
 *   app's default here, because a slot carries no deadline anybody chose and a day recorded on
 *   reconnect is the same day it would have been.
 *
 * ## The clock is the game's, and there is exactly one of it
 *
 * `readAt` and `plannedAt` both come off `GET /games`, so *today* and the horizon are read against
 * one fold — which is the whole of what makes `today + 6` and `planned_at + PLAN_HORIZON`
 * comparable. `GET /plans` deliberately carries no `read_at`: a plan folds nothing against the
 * clock, so there is no second instant for this card to have used by mistake (ADR-0148 §10).
 *
 * ## Held greys the chips and never removes the card
 *
 * A hold stops you writing anywhere another player sees it and **never stops you reading**
 * (ADR-0148 §9). The note that says so is the room's — one note for every refused control on that
 * screen, never one per control — which is the condition 6.2's `disabled` amendment attaches to a
 * greyed chip, and the reason `account_held` draws no coral sentence of its own here.
 */

import { useRef, useState, type RefObject } from 'react';
import { StyleSheet, View } from 'react-native';

import { offlineMessage, type AppError } from '@/shared/errors';
import { BottomSheet, Chip, Note, theme } from '@/shared/ui';

import { HOURS_OFFERED, PLAN_SLOTS, offeredDays, type Plan, type PlanSlot } from '../domain/slots';
import { useSetSlot } from '../hooks/usePlans';

import { DayChips } from './DayChips';
import { HourChips } from './HourChips';
import { planErrorMessage } from './planErrorMessage';
import {
  SAVING,
  SLOT_SHEET_CLOSE,
  SLOT_SHEET_TITLE,
  slotChipLabel,
  slotChipName,
} from './planPresentation';
import { WhereField } from './WhereField';

/** As much of one slot's write as this card reads. Three mutations, one shape. */
interface SlotWrite {
  readonly isPending: boolean;
  readonly isPaused: boolean;
  readonly error: AppError | null;
}

export interface PlanCardProps {
  readonly gameId: string;
  /** When the last seat accepted. The horizon is measured from it. */
  readonly plannedAt: string;
  /** The instant the game list was folded against — **the one clock on this card**. */
  readonly readAt: string;
  /** What has been agreed, and `undefined` where nothing has. The two are one state. */
  readonly plan: Plan | undefined;
  /** The account may not write here. Every chip greys, and the screen owns the one note. */
  readonly refused?: boolean;
}

export function PlanCard({ gameId, plannedAt, readAt, plan, refused = false }: PlanCardProps) {
  const write = useSetSlot();

  /**
   * Which editor the sheet is drawn for, and whether it is up.
   *
   * **One state and not two, and the slot outlives the closing** — a sheet slides out over two
   * hundred milliseconds and its title, its close control's name and its body are all read from
   * the slot, so clearing that on the press would blank the sheet on its way off the screen. It is
   * route-local because it is a fact about a press nobody has made yet.
   */
  const [sheet, setSheet] = useState<{ readonly slot: PlanSlot; readonly open: boolean }>({
    slot: 'where',
    open: false,
  });

  /**
   * What is in the *where* box, and **it outlives the sheet on purpose.**
   *
   * The other two slots commit the value that was pressed, so there is nothing of the player's to
   * lose. A typed note is theirs, and *a refusal puts the words back in the box* is already this
   * app's rule one feature over — so the draft is seeded from the plan when the box is first
   * opened and thrown away only when a write of it has landed.
   */
  const [draft, setDraft] = useState<string | undefined>(undefined);

  /**
   * Each slot's write, keyed by the slot — so a chip reads its **own** state and never the card's.
   *
   * Two slots can genuinely be going out at once: each editor closes on the press, so filling
   * *where* and then tapping a day is two acts and not a double press. A single *is anything in
   * flight* would draw the second chip busy on the first chip's write, which is the one thing a
   * non-optimistic surface must not do — say that a value is being written when it is not.
   */
  const going: Readonly<Record<PlanSlot, SlotWrite>> = {
    where: write.place,
    day: write.day,
    hour: write.hour,
  };

  const paused = PLAN_SLOTS.some((slot) => going[slot].isPaused);

  /**
   * The chip each editor was opened from, so focus goes back to it.
   *
   * Part 13's second modal obligation, and a `View` around the chip rather than a ref on it: the
   * chip is the design system's, `Chip` forwards none, and a required-prop change to a primitive
   * for one caller's benefit is a wider change than this ticket has an argument for.
   */
  const openedFrom: Readonly<Record<PlanSlot, RefObject<View>>> = {
    where: useRef<View>(null),
    day: useRef<View>(null),
    hour: useRef<View>(null),
  };

  /**
   * The coral note's own refusal, and **a hold is not one of them.**
   *
   * `account_held` has a sentence already — the room's amber note, which says what the account is
   * rather than what this tap did — so drawing both would say one fact twice and in two registers.
   */
  const refusal = refused
    ? null
    : (PLAN_SLOTS.map((slot) => going[slot].error).find((one) => one !== null) ?? null);

  function open(slot: PlanSlot): void {
    // The last refusal belonged to the last press. Cleared as the next one is composed, so a
    // sentence about a day never stands under a chip row while somebody is choosing an hour.
    write.place.reset();
    write.day.reset();
    write.hour.reset();

    if (slot === 'where' && draft === undefined) setDraft(plan?.place ?? '');
    setSheet({ slot, open: true });
  }

  const close = () => setSheet((held) => ({ ...held, open: false }));

  return (
    <View style={s.card}>
      <View style={s.row}>
        {PLAN_SLOTS.map((slot) => (
          <View key={slot} ref={openedFrom[slot]}>
            <Chip
              label={slotChipLabel(plan, slot)}
              busyLabel={SAVING}
              accessibilityLabel={slotChipName(plan, slot, { pending: going[slot].isPending })}
              busy={going[slot].isPending}
              disabled={refused}
              onPress={() => open(slot)}
            />
          </View>
        ))}
      </View>

      {refusal === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {planErrorMessage(refusal)}
        </Note>
      )}

      {/* Paused, not pending: the write is held until the connection returns, so the chip's own
          busy word would otherwise be the whole account of a wait with no end in sight. */}
      {paused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

      {/* One sheet, three bodies, keyed by the slot — the shape `SH.saveav` already takes for
          four prompts. Each editor **closes on the press**, so the card behind is what the
          player is looking at when the answer lands. */}
      <BottomSheet
        visible={sheet.open}
        onClose={close}
        title={SLOT_SHEET_TITLE[sheet.slot]}
        closeLabel={SLOT_SHEET_CLOSE[sheet.slot]}
        returnFocusTo={openedFrom[sheet.slot]}
      >
        {sheet.slot === 'where' ? (
          <WhereField
            written={draft ?? ''}
            onChange={setDraft}
            onRecord={() => {
              close();
              write.place.mutate(
                { gameId, written: draft ?? '' },
                // Thrown away only once it has landed, so the next open reads the value the
                // server answered with and a refused one keeps what was typed.
                { onSuccess: () => setDraft(undefined) },
              );
            }}
          />
        ) : null}

        {sheet.slot === 'day' ? (
          <DayChips
            days={offeredDays({ readAt, plannedAt })}
            {...(plan?.day === undefined ? {} : { agreed: plan.day })}
            onPick={(day) => {
              close();
              write.day.mutate({ gameId, day });
            }}
          />
        ) : null}

        {sheet.slot === 'hour' ? (
          <HourChips
            hours={HOURS_OFFERED}
            {...(plan?.hour === undefined ? {} : { agreed: plan.hour })}
            onPick={(hour) => {
              close();
              write.hour.mutate({ gameId, hour });
            }}
          />
        ) : null}
      </BottomSheet>
    </View>
  );
}

const s = StyleSheet.create({
  card: {
    paddingHorizontal: theme.size.gutter,
    paddingVertical: theme.space.sm,
    gap: theme.space.xs,
  },
  // Wrapping rather than scrolling: three chips fit a phone, and the one that can grow is the
  // place — drawn without its court, and taking a second line rather than a gesture on the rare
  // occasion that is still too long.
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});
