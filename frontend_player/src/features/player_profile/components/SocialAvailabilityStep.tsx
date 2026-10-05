/**
 * Step four of onboarding's second part: **when do you usually play?**
 *
 * Seven days by sixteen hours, 07:00 to 23:00, and that is the finest precision this step may
 * produce ([ADR-0189](../../../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
 * §5, mock 36). There is no date, no minute and no calendar on this screen: the grid is the
 * only place a time preference is expressed anywhere in this product, and a precision the
 * domain has nowhere to put would be a promise the player is then held to.
 *
 * A tap toggles one hour; **a press and drag paints a run** — or clears one, if it began on an
 * hour already ticked — because a hundred and twelve hours tapped one by one is not a question
 * anybody finishes.
 *
 * ## It ships empty, and one hour is required to leave it
 *
 * Nothing is ticked on arrival and nothing is ticked on the player's behalf — a pre-seeded hour
 * is a claim the player never made that silently becomes a matchmaking input. That is unchanged
 * and is not the same rule as the floor: **the grid starts blank, and it does not continue
 * blank.**
 *
 * ADR-0102 gave the week a floor of one, because a blank grid was being read as a *measured*
 * zero by a matcher nobody had told, on a question nobody was ever asked. So the forward control
 * is closed at zero — and, because a required answer is not a nudge, the screen says why: the
 * eyebrow carries the rule and the control names what is missing. That is the tag step's settled
 * shape, and it is settled for the same reason — a player facing a dead control deserves the
 * sentence that explains it.
 *
 * **The screen is the grid, and nothing else.** The line under the title, the note about what
 * the week is for, and the footnote under the grid were all cut. `availabilityFootnote` and the
 * promise copy are kept in `availabilityPresentation` — the You tab's *Your week* is where a week
 * is read back and counted, and that is the screen those sentences were really written for.
 *
 * ## Nothing here decides anything
 *
 * What a tap and a drag do, and what a count means, are `availabilityWeek`'s — with their own
 * tests and no renderer — and the geometry and the gesture are `AvailabilityGrid`'s. What is
 * left in this file is which week is on screen and where it is kept. The grid it shares with
 * *Your week* is `WeekGrid`: the control, with the step's chrome left here where it belongs
 * (ADR-0179 §2).
 *
 * ## The week lives in the draft
 *
 * Every tap and every painted run writes through to the part's client-held draft, so walking to
 * step five and back finds the same hours ticked. Nothing is sent anywhere: the draft is in
 * memory until the one commit at the end of the part
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 */

import { useRouter } from 'expo-router';

import { Button } from '@/shared/ui';

import type { WeeklyHour } from '../domain/ProfileDraft';
import { paintCells, toggleCell, weekStanding } from '../domain/availabilityWeek';
import { stepAfter } from '../domain/socialSteps';
import { useProfileDraft } from '../store/profileDraft.store';

import { availabilityContinueLabel, availabilityEyebrow } from './availabilityPresentation';
import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';
import { WeekGrid } from './WeekGrid';

export function SocialAvailabilityStep() {
  const router = useRouter();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('availability');
  const week = draft?.weeklyHours ?? [];
  // The floor is `weekStanding`'s to report and this screen's only to draw. Comparing a
  // length to zero here would be the rule decided a second time, in a `disabled={…}`.
  const standing = weekStanding(week);

  const press = (cell: WeeklyHour) => answer({ weeklyHours: toggleCell(week, cell) });
  // The whole run so far, every time: painting it again from this render's week lands the
  // same hours, so a render behind the finger drops none of them.
  const paintRun = (run: readonly WeeklyHour[], on: boolean) =>
    answer({ weeklyHours: paintCells(week, run, on) });

  return (
    <SocialStepLayout
      step="availability"
      // The rule travels with the position, so a player meets the floor by reading the
      // screen rather than by being stopped by it.
      eyebrow={availabilityEyebrow()}
      action={
        next === undefined ? null : (
          // Closed at zero and open from the first hour — never at a ceiling, because the
          // whole week is a legal answer and the last hour comes off like any other. The
          // label says what is missing rather than leaving the control merely grey.
          <Button
            label={availabilityContinueLabel(standing)}
            size="lg"
            disabled={standing.kind === 'empty'}
            onPress={() => router.replace(SOCIAL_STEP_PATH[next])}
            accessibilityHint={`Goes to ${stepCopy(next).title}`}
          />
        )
      }
    >
      <WeekGrid week={week} onPressCell={press} onPaintCells={paintRun} />
    </SocialStepLayout>
  );
}
