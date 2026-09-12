/**
 * **The plan card** — an eyebrow and a counter, the three slot chips, and *Lock the plan*
 * ([#366](https://github.com/Raketa02/Raketa/issues/366),
 * [#403](https://github.com/Raketa02/Raketa/issues/403),
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3.2) — drawn
 * **in two places**: pinned under the room's header, and in the scroll of the game screen's plan
 * lead ([#414](https://github.com/Raketa02/Raketa/issues/414), ADR-0149 §4 as amended).
 *
 * **Pinned in the room**, because every chat opens at its newest entry — that is what a cursor is
 * for — so a card in the scroll is a card you have to hunt for, and the plan is the thing the room
 * exists to fill. **No panel there**, because the panel that explains the slots is permanent
 * chrome above a composer
 * ([ADR-0145](../../../../../docs/adr/0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md)
 * §6); its home is the game screen, where it is drawn **inside this card** through the `note`
 * slot — between the chips and the button, where the design puts it — and the room passes none.
 * One panel, one home, and the card does not know which surface it is on. It is 5.1's card —
 * `surface`, a 1pt `line` border — and **the border is never an accent**: the mock's coral
 * rectangle is a highlight the author drew, and coral on a card already means pressed.
 *
 * ## `Chip`s on both plan-lead surfaces, `Tag`s on the score lead
 *
 * *A pressable pill is a chip*, *tags are never pressable* — the vocabulary doing exactly what it
 * was split to do (#338 §7). The read-only rendering is a **second component in this feature**
 * rather than an `editable` prop on this one, on `CourtMini` and `CourtBuild`'s own reasoning:
 * here the difference is larger, because one takes three mutations and three input surfaces and
 * the other takes none. ADR-0149 §4 put the read-only one on the game screen wherever the plan is
 * drawn outside the chat; the design reuses **this** card there on the two rungs whose door says
 * *Finish the plan*, and the tags keep the score lead, where the plan is context for a score.
 *
 * ## The lock is an act, and the card draws it as a counter and a control
 *
 * ADR-0144 deleted *Lock it in*, the locked border and the `locked by everybody` pill, and
 * [ADR-0155](../../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)
 * brought one of the three back, on a destination ADR-0144 did not have: the lock **posts a
 * system line into the room** — `{name} locked the plan` — so every member sees the plan was
 * agreed rather than merely completed. **The count and the lock are two facts**: three filled
 * slots is a plan everybody *could* agree, and the lock says somebody did. What the card draws is
 * exactly those two facts — `N of 3 set` in the counter, derived here from the three fields and
 * never sent, and the button that turns the first into the second.
 *
 * The other two stay deleted. **The border does not change** — a locked plan is a word on the
 * counter, `Locked`, and never a colour (Part 13). **`locked by everybody` stays a phrase the data
 * cannot support**: nothing records assent from anyone but the one person who tapped.
 *
 * **The control has four states and `domain/lock.ts` folds them** — greyed below three, live at
 * three, busy while the lock goes out, and **gone** once it has landed rather than 6.1's
 * `settled`, because a second lock records nothing and answers `200`, so a control still offering
 * it would be one that provably does nothing. That file also holds the answer to #324's rule on
 * the greyed control — *a note above it has already said why* — which is that **the counter is the
 * note**: drawn always, directly above the button in sighted and spoken order alike, and stating
 * exactly the count the act is guarded on. The label carries no reason, on the author's own
 * decision.
 *
 * **A lock freezes nothing.** Any member may fill or change any slot, any number of times, before
 * a lock and after one — there is no rate limit, *the line is the friction*, and a move after a
 * lock keeps the lock and writes its own line. **A slot is never emptied**: every chip opens an
 * editor whether or not it already holds a value, and none of the three editors offers a way to
 * clear one. And **there is no unlock**, so the card has nothing to draw about one.
 *
 * ## No optimistic write, and the card is where that is visible
 *
 * *Pending, never optimistic* is this map's rule for everything that reaches another person, and a
 * slot change writes a system line other people read. So the chip goes **busy with the value it
 * already had** — never the value being written — and **the line arrives through the stream like
 * any other entry**, on the nudge every other member's copy of it arrives on. **The lock follows
 * the same rule for the same reason**: the button goes busy with its own word, the counter keeps
 * reading `3 of 3 set` until the server has answered, and the line that confirms it is the
 * stream's.
 *
 * That is also why this card, rather than a sheet, is what reports. Each editor **closes on the
 * press**, so the card is the surface a player is looking at when the answer lands, and it draws
 * three things between the row and the button: the refusal, the pause, and nothing at all when
 * neither — above the control a lock refusal is retried at, and below the two a slot refusal is.
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
 * ## Held greys the chips and the button, and never removes the card
 *
 * A hold stops you writing anywhere another player sees it and **never stops you reading**
 * (ADR-0148 §9). The note that says so is the room's — one note for every refused control on that
 * screen, never one per control — which is the condition 6.2's `disabled` amendment attaches to a
 * greyed chip, and the reason `account_held` draws no coral sentence of its own here. **The room
 * learns of a hold met here off the mutation cache**, through `usePlanWriteRefusals`: this card
 * cannot reach the room's note, and a hold is a fact about the account whichever of the five
 * writes on that screen met it.
 *
 * **Where that note sits is stated rather than assumed**: §3.6 puts it above the composer, and
 * this card is pinned under the header, so the note is **below** these controls in render order
 * and on the same screen as them — both are chrome, neither scrolls — and it is announced as an
 * `alert` the moment the hold lands. That is #366's shape for the chips, inherited by the button
 * and not re-decided here; whether a greyed card wants the note beside it rather than at the
 * composer is a screen-level question for the room, filed with the look this card is owed.
 */

import { useRef, useState, type ReactNode, type RefObject } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage, type AppError } from '@/shared/errors';
import { BottomSheet, Button, Card, Chip, Note, theme } from '@/shared/ui';

import { lockControl } from '../domain/lock';
import { HOURS_OFFERED, PLAN_SLOTS, offeredDays, type Plan, type PlanSlot } from '../domain/slots';
import { useLockPlan, useSetSlot } from '../hooks/usePlans';

import { DayChips } from './DayChips';
import { HourChips } from './HourChips';
import { planErrorMessage } from './planErrorMessage';
import {
  LOCKING,
  LOCK_THE_PLAN,
  SAVING,
  SLOT_SHEET_CLOSE,
  SLOT_SHEET_TITLE,
  THE_PLAN,
  counterLabel,
  planHeadingName,
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
  /**
   * **Drawn between the chips and the button** — the game screen's panel (`PLAN_PANEL`, *Agreed
   * between you — nothing is booked*), inside the card where the design puts it. The room passes
   * none: the panel is not chrome above a composer (ADR-0145 §6). A slot rather than a flag, so
   * the card holds an arrangement and the surface holds what goes in it.
   */
  readonly note?: ReactNode;
}

export function PlanCard({
  gameId,
  plannedAt,
  readAt,
  plan,
  refused = false,
  note,
}: PlanCardProps) {
  const write = useSetSlot();
  const lock = useLockPlan();

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

  const paused = PLAN_SLOTS.some((slot) => going[slot].isPaused) || lock.isPaused;

  /** What the button is — and whether it is drawn at all. `domain/lock.ts` is the fold. */
  const control = lockControl(plan, { pending: lock.isPending });

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
    : ([...PLAN_SLOTS.map((slot) => going[slot].error), lock.error].find((one) => one !== null) ??
      null);

  /**
   * The last refusal belonged to the last press. Cleared as the next one is composed, so a
   * sentence about a day never stands under a chip row while somebody is choosing an hour — and
   * a sentence about the lock never stands above a button somebody is about to press again.
   */
  function clearRefusals(): void {
    write.place.reset();
    write.day.reset();
    write.hour.reset();
    lock.reset();
  }

  function open(slot: PlanSlot): void {
    clearRefusals();

    if (slot === 'where' && draft === undefined) setDraft(plan?.place ?? '');
    setSheet({ slot, open: true });
  }

  function lockThePlan(): void {
    clearRefusals();
    lock.mutate({ gameId });
  }

  const close = () => setSheet((held) => ({ ...held, open: false }));

  return (
    <Card style={s.card}>
      {/* One `header` element for the heading and its count — `YOUR GAMES · n`'s shape. The
          counter is a number, so it is mono and tabular; the pill around it is 6.4's geometry
          with `num.xs` in it, because the tag's own role is sans and 1.4 is categorical. */}
      <View
        accessible
        accessibilityRole="header"
        accessibilityLabel={planHeadingName(plan)}
        style={s.heading}
      >
        <Text style={s.eyebrow}>{THE_PLAN}</Text>
        <View style={s.counter}>
          <Text style={s.counterLabel}>{counterLabel(plan)}</Text>
        </View>
      </View>

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

      {/* The surface's own panel, under the chips and their refusal — the refusal names both
          chips as its remedies, so it stays directly under them — and above the lock. */}
      {note}

      {/* Gone once locked, and greyed under the counter or the room's note — never with a reason
          of its own on the label. `primary` because this is the one act on the card that asks:
          the chips are values and this is the agreement. The card's column stretches it to the
          content width, which is what the mock draws. */}
      {control === 'gone' ? null : (
        <Button
          label={LOCK_THE_PLAN}
          busyLabel={LOCKING}
          busy={control === 'busy'}
          disabled={refused || control === 'greyed'}
          onPress={lockThePlan}
        />
      )}

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
    </Card>
  );
}

const s = StyleSheet.create({
  // 5.1's card and the step between its rows. **Where it sits is the surface's to say** — the
  // room pins it under the header at the gutter, the game screen lays it in a scroll that
  // already is — so no margin lives here.
  card: { gap: theme.space.sm },
  heading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  // 6.4's pill — `line2`, the tag radius, the tag's padding — around a figure rather than a word.
  counter: {
    paddingVertical: theme.space.xxs,
    paddingHorizontal: theme.space.xs,
    borderRadius: theme.radius.tag,
    backgroundColor: theme.color.line2,
  },
  counterLabel: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
  // Wrapping rather than scrolling: three chips fit a phone, and the one that can grow is the
  // place — drawn without its court, and taking a second line rather than a gesture on the rare
  // occasion that is still too long.
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});
