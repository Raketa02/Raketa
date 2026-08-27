/**
 * Step three of onboarding's second part: **when do you usually play?**
 *
 * Seven days by three parts of the day, and that is the finest precision this step may
 * produce. There is no clock time, no hour picker and no date picker on this screen, and
 * there is not going to be one: the grid is the only place a time preference is expressed
 * anywhere in this product, and a precision the domain has nowhere to put would be a
 * promise the player is then held to.
 *
 * ## It ships empty, and one tick is required to leave it
 *
 * Nothing is ticked on arrival and nothing is ticked on the player's behalf — a pre-seeded
 * slot is a claim the player never made that silently becomes a matchmaking input. That is
 * unchanged and is not the same rule as the floor: **the grid starts blank, and it does not
 * continue blank.**
 *
 * ADR-0102 gave the week a floor of one of the twenty-one, because a blank grid was being
 * read as a *measured* zero by a matcher nobody had told, on a question nobody was ever
 * asked. So the forward control is closed at zero — and, because a required answer is not a
 * nudge, the screen says why: the eyebrow carries the rule and the control names what is
 * missing. That is the tag step's settled shape, and it is settled for the same reason —
 * a player facing a dead control deserves the sentence that explains it.
 *
 * **The screen is the grid, and nothing else.** The line under the title, the note about
 * what the week is for, and the footnote under the grid were all cut: seven rows of three
 * ticks are self-evident, and three paragraphs of reassurance around them made the one thing
 * to do on this screen the smallest thing on it. `availabilityFootnote` and the promise copy
 * are kept in `availabilityPresentation` — the profile editor is where a week is read back
 * and counted, and that is the screen those sentences were really written for.
 *
 * ## Nothing here decides anything
 *
 * What a press does, and what a count means, are `availabilityWeek`'s — with their own tests
 * and no renderer — and the geometry is `AvailabilityGrid`'s. What is left in this file is
 * which week is on screen and where it is kept, which is the same split the tags and photos
 * steps made and for the same reason: the profile editor will obey these rules from a screen
 * that looks nothing like this one.
 *
 * ## The week lives in the draft
 *
 * Every press writes through to the part's client-held draft, so walking to step four and
 * back finds the same cells ticked. Nothing is sent anywhere: the draft is in memory until
 * the one commit at the end of the part
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 */

import { useRouter } from 'expo-router';

import { AvailabilityGrid, Button } from '@/shared/ui';

import type { AvailabilitySlot } from '../domain/ProfileDraft';
import {
  DAY_PARTS,
  WEEKDAYS,
  toggleCell,
  isTicked,
  weekStanding,
} from '../domain/availabilityWeek';
import { stepAfter } from '../domain/socialSteps';
import { useProfileDraft } from '../store/profileDraft.store';

import {
  availabilityContinueLabel,
  availabilityEyebrow,
  cellLabel,
  dayLabel,
  dayPartHead,
} from './availabilityPresentation';
import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';

export function SocialAvailabilityStep() {
  const router = useRouter();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('availability');
  const week = draft?.availability ?? [];
  // The floor is `weekStanding`'s to report and this screen's only to draw. Comparing a
  // length to zero here would be the rule decided a second time, in a `disabled={…}`.
  const standing = weekStanding(week);

  const press = (cell: AvailabilitySlot) => answer({ availability: toggleCell(week, cell) });

  return (
    <SocialStepLayout
      step="availability"
      // The rule travels with the position, so a player meets the floor by reading the
      // screen rather than by being stopped by it.
      eyebrow={availabilityEyebrow()}
      action={
        next === undefined ? null : (
          // Closed at zero and open from the first tick — never at a ceiling, because
          // twenty-one is a legal answer and the last cell comes off like any other. The
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
      <AvailabilityGrid
        columnHeads={DAY_PARTS.map(dayPartHead)}
        rows={WEEKDAYS.map((day) => ({
          key: String(day),
          label: dayLabel(day),
          cells: DAY_PARTS.map((part) => ({
            key: `${day}-${part}`,
            selected: isTicked(week, { day, part }),
            onPress: () => press({ day, part }),
            accessibilityLabel: cellLabel({ day, part }),
          })),
        }))}
      />
    </SocialStepLayout>
  );
}
