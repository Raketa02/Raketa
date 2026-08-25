/**
 * Step three of onboarding's second part: **when do you usually play?**
 *
 * Seven days by three parts of the day, and that is the finest precision this step may
 * produce. There is no clock time, no hour picker and no date picker on this screen, and
 * there is not going to be one: the grid is the only place a time preference is expressed
 * anywhere in this product, and a precision the domain has nowhere to put would be a
 * promise the player is then held to.
 *
 * ## It ships empty, and an empty week continues
 *
 * Nothing is ticked on arrival and nothing is ticked on the player's behalf. A pre-seeded
 * slot is a claim the player never made that silently becomes a matchmaking input — so the
 * grid starts blank, the forward control is enabled at zero, and the footnote says what the
 * blank means before it says what it costs. **Blank means no preference, never unavailable**,
 * and it excludes the player from nothing.
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
import { StyleSheet, Text } from 'react-native';

import { AvailabilityGrid, Button, Note, theme } from '@/shared/ui';

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
  AVAILABILITY_PROMISE_BODY,
  AVAILABILITY_PROMISE_TITLE,
  availabilityFootnote,
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

  const press = (cell: AvailabilitySlot) => answer({ availability: toggleCell(week, cell) });

  return (
    <SocialStepLayout
      step="availability"
      action={
        next === undefined ? null : (
          // Never disabled, at zero slots or at twenty-one. A control that made a player
          // tick something to get past would be the step contradicting its own footnote.
          <Button
            label="Continue"
            size="lg"
            onPress={() => router.replace(SOCIAL_STEP_PATH[next])}
            accessibilityHint={`Goes to ${stepCopy(next).title}`}
          />
        )
      }
    >
      <Text style={s.asks}>{stepCopy('availability').asks}</Text>

      {/* `info` rather than `amber`: this explains what the product does with the answer,
          and amber means *watch this, reversible, not yet wrong* — a status about the
          player's own answer rather than an explanation of the app (design-system 1.3). */}
      <Note variant="info" title={AVAILABILITY_PROMISE_TITLE}>
        {AVAILABILITY_PROMISE_BODY}
      </Note>

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
        footnote={availabilityFootnote(weekStanding(week))}
      />
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  asks: { ...theme.type.tiny, color: theme.color.muted },
});
